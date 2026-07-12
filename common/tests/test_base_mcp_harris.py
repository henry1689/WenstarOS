"""测试 base_mcp_harris.py — MCP 基类 + 域配置 + GlobalBusTCPClient"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

def test_domain_config():
    from common.base_mcp_harris import DomainConfig
    cfg = DomainConfig(
        domain_name="test",
        domain_tag="t",
        default_rigid_pool={},
        guard_token_quota=100,
        allow_dynamic_workflow=False,
        subscribe_cross_channel=[],
        allow_cross_domain=False,
    )
    assert cfg.domain_name == "test"
    assert cfg.domain_tag == "t"
    assert cfg.allow_dynamic_workflow is False
    assert cfg.allow_cross_domain is False

def test_domain_config_tianquan():
    """天权域: allow_cross_domain=False for MH-1 compliance"""
    from common.base_mcp_harris import DomainConfig
    cfg = DomainConfig(
        domain_name="天权", domain_tag="t",
        default_rigid_pool={}, guard_token_quota=100,
        allow_dynamic_workflow=True,
        subscribe_cross_channel=["global_alert"],
        allow_cross_domain=False,
    )
    assert cfg.allow_cross_domain is False

def test_domain_config_yaoling():
    """瑶灵域: allow_cross_domain=True for receiving Master commands"""
    from common.base_mcp_harris import DomainConfig
    cfg = DomainConfig(
        domain_name="瑶灵", domain_tag="l",
        default_rigid_pool={}, guard_token_quota=100,
        allow_dynamic_workflow=False,
        subscribe_cross_channel=["global_alert"],
        allow_cross_domain=True,
    )
    assert cfg.allow_cross_domain is True

def test_global_bus_client_create():
    from common.base_mcp_harris import GlobalBusTCPClient
    client = GlobalBusTCPClient("test-domain")
    assert client.domain_tag == "test-domain"
    assert client.connected is False
    assert client.host == "127.0.0.1"
    assert client.port == 9100

def test_global_memory_retriever():
    import asyncio
    from common.base_mcp_harris import GlobalMemoryRetriever
    retriever = GlobalMemoryRetriever()
    result = asyncio.run(retriever.search([0.1]*32, "tianquan", 5))
    assert "result" in result
