"""
executor/ — 天权域工作流节点执行器注册中心
=============================================
将 YAML 工作流中的 node_id 映射到真实 Python 函数。
每个执行器函数签名: async fn(node: AgentNode, ctx: WorkflowContextV2) -> dict
"""

from .node_executors import (
    create_executor,
    EXECUTOR_REGISTRY,
    execute_node,
    list_executors,
)

__all__ = [
    "create_executor",
    "EXECUTOR_REGISTRY",
    "execute_node",
    "list_executors",
]
