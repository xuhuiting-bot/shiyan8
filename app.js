// 引入Express框架
const express = require('express');
// 创建Express应用实例
const app = express();

// 创建一个GET请求的测试接口，这里的路径是 /test，你可以根据需求自行修改路径
app.get('/test', (req, res) => {
    // 使用res.send方法返回固定消息，这里返回 'Backend is connected!'，你也可以改成其他想要返回的内容
    res.send('Backend is connected!');
});

// 定义服务器监听的端口号，这里使用3000端口，你可以根据实际情况修改端口号
const port = 3000;
// 让服务器开始监听指定端口，当有请求到达对应接口时就会进行处理
app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});