# Tekton + GitLab + Harbor + ArgoCD 全流程 CI/CD Demo

这个仓库提供一个可直接落地的示例，目标场景与你当前环境一致：

- Kubernetes: `3 master + 3 worker`
- ArgoCD: 已部署
- Harbor: `10.0.0.41`
- GitLab: `10.0.0.200`

示例应用使用 **Python FastAPI**（带完整 CRUD + 健康检查 + 单元测试），并通过 Tekton 完成：

1. 拉取 GitLab 代码
2. 执行 `pytest`
3. 用 Kaniko 构建镜像并推送 Harbor
4. 自动更新 GitOps 清单中的镜像标签
5. 推送回 GitLab
6. 由 ArgoCD 自动同步到 Kubernetes

---

## 1. 仓库结构

```text
.
├── app/                         # FastAPI 应用
├── tests/                       # pytest 测试
├── Dockerfile
├── requirements*.txt
├── gitops/                      # GitOps 清单（ArgoCD 监听）
│   ├── base/
│   └── overlays/dev/
├── tekton/
│   ├── tasks/                   # 自定义 Task（clone/test/build/update）
│   ├── pipelines/               # Pipeline 和手动 PipelineRun
│   └── triggers/                # TriggerTemplate/Binding/EventListener
├── k8s/
│   ├── namespaces.yaml
│   ├── pipeline-rbac.yaml
│   ├── harbor-secret.yaml       # 需填真实凭据
│   ├── gitlab-secret.yaml       # 需填真实凭据
│   └── argocd-application.yaml
└── scripts/
    ├── bootstrap.sh             # 一键部署基础资源
    └── gitlab-push-sample.json
```

---

## 2. 前置条件

- 已安装 `kubectl`
- 集群已安装 Tekton Pipelines 和 Tekton Triggers
- 集群能访问：
  - `http://10.0.0.200`（GitLab）
  - `harbor10.0.0.41`（Harbor 域名能解析）
- ArgoCD 已安装在 `argocd` 命名空间

> 如果 Harbor 使用自签名证书，需要为 Kaniko 节点/容器配置信任，或使用 HTTP（不推荐生产）。

---

## 3. 准备 GitLab 项目

1. 在 GitLab 新建仓库，例如：`root/teketondemo`
2. 把本仓库代码推送到：
   - `http://10.0.0.200/root/teketondemo.git`
3. 确保 `main` 分支可推送（Tekton 会回写 `gitops/overlays/dev/kustomization.yaml`）

---

## 4. 配置凭据

### 4.1 Harbor 凭据

编辑 `k8s/harbor-secret.yaml`：

- 将 `<BASE64_DOCKER_CONFIG_JSON>` 替换为 `~/.docker/config.json` 的 base64（单行）

示例生成命令：

```bash
cat ~/.docker/config.json | base64 -w 0
```

### 4.2 GitLab 凭据

编辑 `k8s/gitlab-secret.yaml`：

- `username`: GitLab 用户（示例是 `root`）
- `password`: 建议使用 Personal Access Token

---

## 5. 部署流水线与 GitOps

```bash
./scripts/bootstrap.sh
kubectl apply -f k8s/harbor-secret.yaml
kubectl apply -f k8s/gitlab-secret.yaml
```

检查资源：

```bash
kubectl get task,pipeline,eventlistener -n cicd
kubectl get application -n argocd
```

---

## 6. 方式一：手动触发 PipelineRun

```bash
kubectl apply -f tekton/pipelines/pipelinerun-manual.yaml
kubectl get pipelineruns -n cicd
kubectl logs -f -n cicd $(kubectl get pods -n cicd -l tekton.dev/pipelineRun -o name | head -n1)
```

成功后应看到：

- Harbor 出现镜像：`harbor10.0.0.41/library/tekton-demo-api:<tag>`
- GitLab 中 `gitops/overlays/dev/kustomization.yaml` 的 `newTag` 被更新
- ArgoCD 自动同步 `tekton-demo` 命名空间

---

## 7. 方式二：GitLab Webhook 自动触发

### 7.1 暴露 EventListener

已提供 NodePort：`30080`

```bash
kubectl get svc -n cicd tekton-demo-listener-nodeport
```

Webhook URL（示例）：

```text
http://<任一K8s节点IP>:30080
```

### 7.2 配置 GitLab Webhook

在 GitLab 项目中配置：

- URL: 上述 NodePort 地址
- Trigger: Push events
- Content type: `application/json`

推送代码后，查看：

```bash
kubectl get pipelineruns -n cicd -w
```

---

## 8. 应用验证

等待 ArgoCD 同步完成后：

```bash
kubectl get deploy,svc,ingress -n tekton-demo
kubectl port-forward -n tekton-demo svc/tekton-demo-api 18080:80
```

本地测试：

```bash
curl http://127.0.0.1:18080/healthz
curl -X POST http://127.0.0.1:18080/todos -H 'Content-Type: application/json' -d '{"title":"learn tekton","done":false}'
curl http://127.0.0.1:18080/todos
```

---

## 9. 常见问题

### Q1: Kaniko 推送 Harbor 401

- 检查 `harbor-auth` secret 内容
- 检查 Harbor 项目权限（`library` 是否允许推送）
- 检查镜像地址与 Harbor 实际项目路径一致

### Q2: 更新 GitOps 失败（push rejected）

- 检查 `gitlab-auth` token 是否具备写权限
- 检查 `main` 分支保护策略（是否禁止机器人账号推送）

### Q3: ArgoCD 不同步

- 检查 `Application` 的 `repoURL/path/targetRevision`
- 检查 ArgoCD 是否可访问 GitLab
- 手动 `argocd app sync tekton-demo-api`

---

## 10. 本地开发与测试

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
uvicorn app.main:app --reload --port 8080
```

---

## 11. 你可以继续扩展的方向

- 引入 SonarQube 代码扫描
- 引入 Trivy 镜像扫描任务
- 多环境（dev/stage/prod）+ 不同 overlay
- 使用 Tekton Chains 产出供应链签名（SLSA）

