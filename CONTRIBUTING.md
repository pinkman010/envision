# 贡献指南

感谢您对ESG智能分析系统的关注！我们欢迎各种形式的贡献。

## 如何贡献

### 报告问题

如果您发现了bug或有功能建议，请通过Issue提交。

**提交Issue前请检查：**
- [ ] 搜索现有Issue，避免重复
- [ ] 使用Issue模板
- [ ] 提供详细的复现步骤
- [ ] 附上相关日志或截图

### 提交代码

1. **Fork项目**
   ```bash
   git clone https://github.com/pinkman010/envision.git
   cd envision
   ```

2. **创建分支**
   ```bash
   git checkout -b feature/your-feature-name
   # 或
   git checkout -b fix/your-bug-fix
   ```

3. **开发**
   - 遵循代码规范
   - 编写测试
   - 更新文档

4. **提交代码**
   ```bash
   git add .
   git commit -m "feat(module): description"
   git push origin feature/your-feature-name
   ```

5. **创建Pull Request**
   - 填写PR模板
   - 关联相关Issue
   - 等待代码审查

## 代码规范

### Python代码规范

- 遵循PEP 8
- 使用类型注解
- 编写文档字符串
- 最大行长度100字符
- 函数复杂度不超过15

### 提交信息规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型：**
- `feat`: 新功能
- `fix`: 修复
- `docs`: 文档
- `style`: 格式
- `refactor`: 重构
- `perf`: 性能
- `test`: 测试
- `chore`: 构建

## 开发流程

1. 阅读[开发指南](./docs/DEVELOPMENT.md)
2. 设置开发环境
3. 编写代码和测试
4. 运行代码检查
5. 提交Pull Request

## 代码审查

所有代码都需要经过审查才能合并。

**审查标准：**
- 代码质量
- 测试覆盖
- 文档完整
- 性能影响
- 安全考虑

## 许可证

通过贡献代码，您同意将其授权给项目使用的许可证。

## 联系方式

- 项目维护者：[团队邮箱]
- 讨论区：GitHub Discussions

感谢您的贡献！
