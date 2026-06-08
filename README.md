# 基于Python+EdgeWebdriver处理网页自动化

### 1. 打开标签页

- https://peoplego.vankeservice.com/#/Embed/visitorReview/pending?phone=18208475905&name=%E8%8A%B1%E6%A2%A6%E8%8E%B2&id=2462900&projectCode=52010017

### 2. 点击元素 div.van-tab:nth-child(2)

- 等待选择器最多5000ms，如果点击成功后延迟800毫秒

### 3. 点击元素 div.van-tab:nth-child(1)

- 等待选择器最多5000ms，如果点击成功后延迟3000毫秒

### 4. 判断元素是否存在 button.van-button--primary

- 如果不存在，则延迟300ms后进入步骤7
- 如果存在，则延迟300ms后进入步骤5

### 5. 点击元素 button.van-button--primary

- 等待选择器最多5000ms，如果点击成功后延迟400毫秒

### 6. 点击元素 button.van-dialog__confirm

- 等待选择器最多5000ms，如果点击成功后延迟3000毫秒

### 7. 关闭标签页，然后回到步骤1循环



#### 注：

#### 1. 如果过程中因网络或服务器或其他原因导致出错，统一跳转至步骤7，进入下一轮循环

#### 2. 这是一个7x24h无间断运行的项目，需要整个流程中有充足的异常情况处理机制，用try except包裹