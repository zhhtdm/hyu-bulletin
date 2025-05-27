# hyu-bulletin
- 将汉阳大机械系、国际处新发公告标题翻译后推送至订阅邮箱
- 提供一个网页用于[设置服务参数](#设置)
- 使用[`MongoDB`](https://www.mongodb.com/)存储以下数据：
  - 已处理过的公告`id`
  - 订阅邮箱列表
  - 服务的设置参数

## 设置
登录[`http(s)://service.domain/path/settings/`]()可配置服务，包括：
- 开启或关闭服务
- 设置每日抓取次数上下限

## 项目环境变量（.env）

在项目根目录下创建`.env`文件，`MongoDB`、`SMTP`服务和百度翻译`API`相关的项必须填写，其他项可以省略，示例:

```
MONGODB_CLIENT_URL="mongodb+srv:...."
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_EMAIL=you@example.com
SMTP_PASSWORD=yourpassword
BAIDU_APP_ID=123
BAIDU_APP_KEY=abc
PORT=8000
HOST=127.0.0.1
APP_PATH=""
```
