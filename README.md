# Tekton + GitLab + Harbor + ArgoCD 全流程 CI/CD（进阶版 Demo）

> 面向你的环境：`3 master + 3 worker` K8s、ArgoCD 已部署、Harbor `10.0.0.41`、GitLab `10.0.0.200`。

这次不是简单 hello-world，而是一个更接近生产的后端服务：

- **FastAPI + SQLAlchemy**
- **JWT 登录鉴权**
- **多资源模型**：用户、项目、任务
- **任务状态流转**：`todo / in_progress / done`
- **分页/过滤接口**
- **pytest 自动化测试**
- Tekton 完整流水线：测试 → 镜像构建推送 Harbor → 更新 GitOps tag → ArgoCD 自动部署

---

## 1. 功能说明（应用层）

API 包括：

- `POST /auth/register` 用户注册
- `POST /auth/login` 用户登录（返回 JWT）
- `POST /projects` 创建项目（需登录）
- `GET /projects` 项目列表（支持分页）
- `POST /projects/{project_id}/tasks` 创建任务（需登录）
- `GET /projects/{project_id}/tasks?status=in_progress` 按状态过滤
- `PATCH /projects/{project_id}/tasks/{task_id}` 局部更新任务
- `GET /healthz` 健康检查

---

## 2. 目录结构

```text
.
├── app/
│   ├── config.py
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   ├── security.py
│   └── routers/
│       ├── auth.py
│       ├── projects.py
│       └── tasks.py
├── tests/
│   ├── conftest.py
│   └── test_api_flow.py
├── Dockerfile
├── requirements*.txt
├── gitops/
├── tekton/
├── k8s/
└── scripts/
```

---

## 3. Tekton 流水线设计

Pipeline：`tekton-demo-cicd`

1. `git-clone-local`：拉 GitLab 代码
2. `python-test`：安装依赖并执行 `pytest -q`
3. `build-and-push`：Kaniko 构建镜像并推送 Harbor
4. `update-gitops-tag`：更新 `gitops/overlays/dev/kustomization.yaml` 的 tag，并 push 回 `main`
5. ArgoCD 检测 Git 变更，自动部署到 `tekton-demo` namespace

---

## 4. 部署前准备

- 已安装：`kubectl`
- 集群已安装：Tekton Pipelines + Tekton Triggers
- 集群网络可达：
  - `http://10.0.0.200`
  - `10.0.0.41`

将代码推到你的 GitLab 仓库，例如：

```text
http://10.0.0.200/gitops/teketondemo.git
```

---

## 5. 配置密钥

### 5.1 Harbor 凭据

编辑 `k8s/harbor-secret.yaml` 的：

- `.dockerconfigjson: <BASE64_DOCKER_CONFIG_JSON>`

生成方式：

```bash
cat ~/.docker/config.json | base64 -w 0
```

### 5.2 GitLab 凭据

编辑 `k8s/gitlab-secret.yaml`：

- `username`: 可推送仓库的 GitLab 用户
- `password`: PAT（推荐）或密码

---

## 6. 部署命令

```bash
./scripts/bootstrap.sh
kubectl apply -f k8s/harbor-secret.yaml
kubectl apply -f k8s/gitlab-secret.yaml
```

检查：
检查资源：

```bash
kubectl get task,pipeline,eventlistener -n cicd
kubectl get application -n argocd
```

---

## 7. 手动触发一次 CI/CD

```bash
kubectl create -f tekton/pipelines/pipelinerun-manual.yaml
kubectl get pipelineruns -n cicd
```

查看运行日志（任选 pipeline pod）：

```bash
kubectl get pods -n cicd
kubectl logs -n cicd <pod-name> -c step-unit-test
```

成功标志：

- Harbor 出现新镜像 tag
- `gitops/overlays/dev/kustomization.yaml` 的 `newTag` 被 Tekton 自动更新并提交
- ArgoCD App 自动 Sync

---

## 8. GitLab Webhook 自动触发

EventListener 已通过 NodePort `30080` 暴露：

```bash
kubectl get svc -n cicd tekton-demo-listener-nodeport
```

GitLab Webhook：

- URL：`http://<任意K8s节点IP>:30080`
- Trigger：Push events
- Content-Type：`application/json`

推送代码后观察：

```bash
kubectl get pipelineruns -n cicd -w
```

---

## 9. 部署后接口验证

```bash
kubectl port-forward -n tekton-demo svc/tekton-demo-api 18080:80
```

### 9.1 健康检查

```bash
curl http://127.0.0.1:18080/healthz
```

### 9.2 注册 + 登录

```bash
curl -X POST http://127.0.0.1:18080/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"alice","email":"alice@example.com","password":"Passw0rd!"}'

TOKEN=$(curl -s -X POST http://127.0.0.1:18080/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=alice&password=Passw0rd!' | jq -r .access_token)
```

### 9.3 创建项目和任务

```bash
curl -X POST http://127.0.0.1:18080/projects \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d '{"name":"platform","description":"tekton cicd"}'
```

---

## 10. 本地测试

```bash
curl http://127.0.0.1:18080/healthz
curl -X POST http://127.0.0.1:18080/todos -H 'Content-Type: application/json' -d '{"title":"learn tekton","done":false}'
curl http://127.0.0.1:18080/todos
```

---


## 11. 后续可继续增强

- 增加 `alembic` 数据库迁移
- 增加 `Trivy` 镜像安全扫描 Task
- 增加 `SonarQube` 代码扫描
- 细分多环境 `dev/stage/prod` 与审批门禁
