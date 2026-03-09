# 常见问题 (FAQ)

## 1. 系统部署

### Q: 如何部署系统？
A: 请参考《部署说明文档.md》，使用pip安装依赖后手动启动服务。

### Q: 需要哪些环境依赖？
A: Python 3.10+, Ollama (本地嵌入模型)

### Q: 如何配置大模型API？
A: 在.env文件中配置LLM_API_KEY和LLM_BASE_URL。

## 2. 功能使用

### Q: 支持哪些文件格式？
A: PDF (.pdf) 和 Word (.docx)

### Q: 最大支持多大的文件？
A: 默认50MB，可在.env中修改MAX_FILE_SIZE配置

### Q: 如何添加新的ESG议题？
A: 在templates/rule_templates/topic_rules.json中添加

### Q: 如何修改相似度阈值？
A: 在.env中修改SIMILARITY_THRESHOLD配置

## 3. 数据安全

### Q: 数据存储在哪里？
A: 数据存储在本地：
- 向量数据: ./data/chroma_db
- 结构化数据: ./data/esg_system.db

### Q: 数据会上传到云端吗？
A: 不会。所有数据本地存储，嵌入模型也使用本地Ollama部署。

### Q: 如何备份数据？
A: 定期备份./data目录即可。

## 4. 故障排查

### Q: 上传文件失败怎么办？
A: 检查：
1. 文件格式是否正确（PDF/Word）
2. 文件大小是否超过限制
3. 文件是否损坏

### Q: LLM调用失败怎么办？
A: 检查：
1. LLM_API_KEY是否正确配置
2. 网络连接是否正常
3. LLM服务是否可用

### Q: 向量数据库初始化失败怎么办？
A: 检查：
1. Ollama服务是否启动
2. OLLAMA_BASE_URL配置是否正确
3. 磁盘空间是否充足

## 5. 合规相关

### Q: AI生成的内容可以直接使用吗？
A: 不可以。所有AI输出仅为辅助参考，需经人工复核确认后方可使用。

### Q: 如何保证数据不可篡改？
A: 所有操作记录审计日志，日志带SHA-256哈希，可验证完整性。

### Q: 系统符合哪些ESG标准？
A: 支持ISSB、SASB、HKEX等主流ESG披露标准。

## 6. 性能优化

### Q: 如何提高处理速度？
A: 1. 增加EMBEDDING_MAX_WORKERS配置
   2. 使用更高配置的机器
   3. 优化网络连接

### Q: 如何减少内存占用？
A: 1. 减小CHUNK_SIZE配置
   2. 定期清理历史数据
   3. 使用更小的嵌入模型

## 7. 扩展开发

### Q: 如何添加新的Agent？
A: 1. 继承BaseAgent类
   2. 实现_execute方法
   3. 在router.py中注册路由
   4. 在app.py中添加页面

### Q: 如何修改Prompt模板？
A: 在templates/prompt_templates/目录下修改对应的.j2文件

### Q: 如何添加新的ESG标准？
A: 在templates/rule_templates/esg_standards.json中添加
