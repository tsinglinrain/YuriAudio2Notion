# 参数

## 饭角element提取

name
description
horizontal, 废弃, 之前是api不支持，现在是太模糊了, 不合适
publish_date
update_frequency
ori_price
author_name

## Notion property设置

Name
简介
Cover
Publish Date
更新
Price
原著

商剧

## 代码post参数

保持和饭角一致


# 其他

离谱, url file无法预览的, 只能以附件的形式进行存储, 然后展示链接, 效果较差

这一步如果实现不了, 我甚至都不想继续提取了

可以通过图床, 进行上传, 但是图床费钱, 不如直接下载上传了.

我的方法是微信打开小程序, 然后下载, 随后上传.

# 时间参看

[Notion page-property](https://developers.notion.com/reference/page-property-values#files)

其他property也是这个链接

# 完成情况

- [x] 基本完成, 已经能够完成工作流,

- [x] 但是, 需要将base url隐藏, achieved

- [x] 需要将类改成可以更新, achieved

    Tag其实也可从简介部分分析, 如纯爱, 古风等. achieved

    prompt, 对于诸如"全一季现代纯爱广播剧《有趣》""全一季科幻悬疑百合广播剧《离开与你相遇的世界》""现代纯爱广播剧《帮我拍拍》第一季"等字符串，想要提取每一个的tag，如'全一季""现代""纯爱".需要注意的是，每个字符串"广播剧《"前面内容都是未知的,如何提取呢？

- [x] GitHub项目, 中文分词太重, 不合适
- [x] 直接取吧. achieved

- [x] up主也可从简介中提取, achieved

- [x] 注意, `main`函数没有修改, achieved

- [x] main函数以及调试函数, 大量函数重复, 可以用类封装, achieved

- [x] 正剧的剧集数也可以传入, 抓"正剧", achieved

- [x] 用ts重写一个, 练练手, doing

- [x] webhook, 但是Notion似乎不支持, achieved, 但继续

- [x] docker部署, 上传至Docker Hub, achieved

- [x] 网页端开放一个接口, 输入剧集连接就能解析, 这个还是算了, 不做

- [x] api抓取的, 有一些是`已完结`, `完结`, 最好是`已完结`, achieved

- [x] 每周四几点几点, 每周四更新, 周六更新, 这些全部改成统一格式. 统一格式为`每周一更新`,
`每周一每周四更新`,需要改成`每周一更新`和`每周四更新`, achieved

- [x] 具体时间暂时不做抓取, 数据库中创建新的属性, 手动填入

- [ ] 真是离谱, 这个竟然是上传的时候大家自己填写的

- [ ] 主役和饰演的角色的颜色不一致, 如果能一一对应就好了, 需要查询一下接口

- [x] 增添`Album Link`这个属性, achieved

# icon获取方法

1. 打开任意`page`
2. `/`呼出菜单后,键入`emoji`,选择`Emoji`后弹出emoji菜单
3. 选择需要的`emoji`
4. 复制过来🎧(emoji不一样, 不要紧, 上传上去都是一样的)不一样是各个客户端显示得不一样.

# webhook的进一步强化

- [x] database中设置按钮, 在property中键入url的内容后, 点击按钮即可在当前的数据库中, achieved

- [x] 可能需要对兼容性和美观性做进一步的取舍, 需要单独添加一个url的property,
定义为`Upload url`, achieved

- [x] 对目前代码进行进一步重构, 可以参考之前`rsshub`的写法, achieved

- [x] 舍弃再docker中写入环境变量的写法, 改为从当前界面的按钮中获取当前数据据的`database id`, achieved

```python
database_id = data["data"]["parent"]["database_id"]
```

# 分支合并

两个分支合并到main分支, 有点困难, 部分文件可能需要改成比较合适的名字

`yuri.soyet.icu`的这个似乎用不上,感觉可以做一个备份即可.

Claude prompt

请为我评估:1.当前分支下的文件命名的是否符合规范.部分文件说明如下,`main.py`为本地下直接运行该函数达成的目标,`main.button`由`main.py`修改得到,为`flask_post.py`服务,在`Dockerfile`中可以体现.`local_main`为`flask_main.py`服务,为add-flask分支的文件,在add-flask分支的`Dockerfile`中可以体现.

## 安全设置

为防止未授权使用, webhook 接口现已添加 API 密钥验证。使用时请按照以下步骤配置：

1. 在 `.env` 文件中添加 `API_KEY=your_secure_key`（替换为你自己的安全密钥）
2. 在发送请求时,在请求头中添加 `YURI-API-KEY` 或在查询参数中添加 `api_key`

示例 (使用请求头):
```python
import requests

response = requests.post(
    url="http://your-server:5050/webhook-url",
    json={"url": "your_url_here"},
    headers={"YURI-API-KEY": "your_secure_key"}
)
```

示例 (使用查询参数):
```
http://your-server:5050/webhook-url?api_key=your_secure_key
```

如果未配置 API_KEY, 系统将记录警告日志, 但仍会允许请求通过 (不推荐在生产环境中这样设置)。

假如这破项目真有人看, 我建议你也加上. 

# post请求的增强

对于notion database的post请求目前还是只能在Notion端执行测试，过于繁琐，应当仿照Notion的post请求格式，自己在本地请求, 
- [x] database achieved, 
- [ ] page尚未

# 交流

喜欢百广, 用Notion, 想用Notion整理, 我觉得三个凑齐的人少之又少.

本质上一些api还是抓取出来的, 一方面害怕铁拳, 另一方面不希望被人滥用, 所以如果你看到这里, 请心照不宣.

如果你看到这里, 希望这个小项目能为你带来帮助. 有不正确之处, 欢迎指出, pr.

如果你对代码有些不懂之处, 欢迎提问.

最后感谢一下zhufree老师, 之前在抓取上有不懂的地方, 问了.


## 其他碎碎念

- 想做关于cv的细致介绍, 但是这个本身就是繁琐的信息收集。而且现在存在, 如"萌娘百科", 已经有人做的很好了，只是会把所有作品放上去，而非专门的cv。至于漫展等基本微博就有，我也不知道有没有这个必要。我不知道我的意义是什么。
- 毕设压力好大, 很久没维护这个项目了
- 今天给这个项目修一修, 主要是Notion API更新了新版本, 需要去维护一下, `database` -> `data_source`
- 我基本上就是看到有什么新的剧作了, 打开https://baihehub.com, 点进去新剧, 找到`album_id`, 然后填到database里面，然后公式计算, 随后复制网址，再次复制到post_url, 随后点击按钮, 等一会就全部抓取并填充进去了, 好了。
- 最近《神龛》是真不错, 如果还有饭角年度广播剧评选, 我觉得这个拿第一没问题。然后是《月光找不到》第二，第三难说了。
- 我现在应该判断传入的是网址还是id, 算了我感觉网址就没什么用
- 直接id得了


## 继续维护
- [ ] 先data_source, 修改好后commit, 不能一起改, 维持一下干净点的commit, 养成好点的习惯
  - 看了半天，原来是webhook版本的实现思路是更新界面, 所以和`data_source`根本没有关系,
  - 也就是说根本不用改

# Acknowledgement

[zhufree (zhufree)](https://github.com/zhufree)

[首页 Home | 百合Hub](https://baihehub.com/)
