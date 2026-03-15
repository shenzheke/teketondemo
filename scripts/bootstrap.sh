#!/usr/bin/env bash
set -euo pipefail

kubectl apply -f k8s/namespaces.yaml
kubectl apply -f k8s/pipeline-rbac.yaml
kubectl apply -f tekton/tasks/
kubectl apply -f tekton/pipelines/cicd-pipeline.yaml        # ← 只 apply Pipeline
kubectl apply -f tekton/triggers/
kubectl apply -f k8s/argocd-application.yaml

echo "Bootstrap completed."
