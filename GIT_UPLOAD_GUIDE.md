# Git上传指南

## 项目中的大文件

在这个Neo4j项目中，我们发现了以下超过GitHub 100MB限制的大文件：

```
393M    /Users/shenjunhua/Documents/neo4j/model/chinese-roberta-wwm-ext/pytorch_model.bin
391M    /Users/shenjunhua/Documents/neo4j/model/best_roberta_rnn_model_ent_aug.pt
390M    /Users/shenjunhua/Documents/neo4j/model/chinese-roberta-wwm-ext/tf_model.h5
390M    /Users/shenjunhua/Documents/neo4j/model/chinese-roberta-wwm-ext/flax_model.msgpack
 52M    /Users/shenjunhua/Documents/neo4j/finetune_demo/questions.csv
 45M    /Users/shenjunhua/Documents/neo4j/data/medical.json
 44M    /Users/shenjunhua/Documents/neo4j/data/ner_data_aug.txt
 43M    /Users/shenjunhua/Documents/neo4j/data/medical_new_2.json
 25M    /Users/shenjunhua/Documents/neo4j/finetune_demo/peft_data.txt
 25M    /Users/shenjunhua/Documents/neo4j/data/lora_data/train.json
```

## 解决方案

为了确保您能够顺利上传项目到Git仓库，我们提供了两种解决方案：

### 方案1：使用.gitignore忽略大文件（简单方法）

我们已经创建了一个`.gitignore`文件，它会自动忽略上述大文件。这意味着这些文件不会被上传到Git仓库中。

使用这种方法的步骤：

1. 确保`.gitignore`文件在项目根目录中
2. 正常进行Git操作：

```bash
git add .
git commit -m "初始提交"
git push
```

**注意**：使用这种方法，其他人克隆您的仓库后将无法获取这些被忽略的大文件。您需要另外提供这些文件的下载方式。

### 方案2：使用Git LFS处理大文件（推荐方法）

如果您希望将大文件也包含在Git仓库中，可以使用Git Large File Storage (LFS)。我们已经创建了一个`.gitattributes`文件来配置Git LFS。

使用Git LFS的步骤：

1. 安装Git LFS

```bash
# macOS (使用Homebrew)
brew install git-lfs

# 其他系统请参考: https://git-lfs.github.com/
```

2. 在项目中设置Git LFS

```bash
cd /Users/shenjunhua/Documents/neo4j  # 进入项目目录
git lfs install  # 初始化Git LFS
```

3. 确保`.gitattributes`文件在项目根目录中

4. 正常进行Git操作：

```bash
git add .
git commit -m "初始提交"
git push
```

**注意**：使用Git LFS需要确保您的Git托管服务支持LFS，并且可能有存储限制。GitHub提供1GB的免费LFS存储空间，超出部分需要付费。

## 其他建议

如果您不需要这些大文件，可以考虑：

1. 提供这些文件的下载链接，而不是直接包含在仓库中
2. 使用模型压缩技术减小模型文件的大小
3. 将大数据文件拆分成更小的部分
4. 使用外部存储服务（如Google Drive、百度网盘等）存储大文件

## 检查大文件

如果您想检查项目中的大文件，可以使用以下命令：

```bash
find /path/to/your/project -type f -not -path "*/\.git/*" -exec du -h {} \; | sort -rh | head -n 10
```

这将显示项目中最大的10个文件。

## 参考资料

- [Git LFS官方文档](https://git-lfs.github.com/)
- [GitHub大文件处理指南](https://docs.github.com/cn/repositories/working-with-files/managing-large-files)