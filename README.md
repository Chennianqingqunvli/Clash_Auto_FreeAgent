# Clash_Auto_FreeAgent
这个项目是一个轻量级的 IP2FREE 辅助工具：用 Python 登录 IP2FREE 接口，自动拉取最新的免费代理列表，生成符合 Clash 配置格式的 YAML 并保存到桌面（按日期命名）。内置的 HTML 和 JS 文件是从 IP2FREE 官网保存的快照，便于参考界面结构。运行前只需在环境变量里设置 IP2FREE_EMAIL 和 IP2FREE_PASSWORD，执行 python ip2free_agent.py 即可生成可直接使用的代理配置，同时仓库已忽略生成的 YAML，避免误提交敏感信息。
