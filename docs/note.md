# 基本参数

## 饭角element提取

name

description

horizontal, 废弃, 之前是api不支持，现在是太模糊了, 不合适

publish_date

update_frequency

ori_price

author_name

## Notion property 名字设置

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


# 海报封面相关

离谱, url file无法预览的, 只能以附件的形式进行存储, 然后展示链接, 效果较差

这一步如果实现不了, 我甚至都不想继续提取了

可以通过图床, 进行上传, 但是图床费钱, 不如直接下载上传了.

我的方法是微信打开小程序, 然后下载, 随后上传.

- [x] 后续Notion的API支持file上传, 已经解决.....

# 时间参看

[Notion page-property](https://developers.notion.com/reference/page-property-values#files)

其他property也是这个链接

# 最早项目构建完成情况

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
- [x] 先data_source, 修改好后commit, 不能一起改, 维持一下干净点的commit, 养成好点的习惯
  - 看了半天，原来是webhook版本的实现思路是更新界面, 所以和`data_source`根本没有关系,
  - 也就是说根本不用改

- [x] 我真的服了，明明什么都没改，怎么docker 镜像拉去之后就是运行不了.....
  - [x] 原来是服务端docker compose文件没改，服了

就这样吧，感觉差不多了....

还可以继续优化


- [x] 改成获取`FanjiaoAlbumID`, 因为以后拓展的话

不是，怎么漫播的广播剧全部下架了? 想听听雨眠的，直接没了

我写的代码原文就没有`url`, 依赖输入....好吧，感觉没有修改的必要了

- [x] 改成id，url的处理放到前置

- [ ] `webhook_data_source`就改了者这个一个，其余懒得改了，真不想改了，反正我也只用这个


# 业务扩展

## 歌曲方面

目前来看，还是选择参数为网址，更为方便
歌词的提取大概是需要一个从饭角分享粘贴连接，复制进QQ，然后复制至Notion的过程

很多代码可以复用

优先提取

## 其他

- update需要提上日程了, 我发现horizontal效果更好

- 测试了一下，部分horizontal以及square是原本cover的部分截取，分辨率很低。

- 总而言之，海报还是得看竖版的

- 歌曲的海报有些是没有的，需要进行更改

- cover是一定存在的的，但是square,horizonnal不一定存在

## 本次音乐相关提取方面

- [x] 音乐cover统一上传square

歌词存在两个部分
description
subtitle

- [x] description可以直接写
- [ ] subtitle需要先下载，再读取，中间还涉及提取，暂不考虑

- [x] 能在线读取吗？

    读取不了

- [x] 目前上传部分代码基本完成, 但是description部分拆分不了。只能手动进行拆分。

- [ ] 图片icon，似乎只能emoji, 没有解决办法。
  - [ ] 找到解决办法了，实际上Retrieve_a_data_source,久能发现其实一个图床连接，没有什么规律性，需要retrieve

# 更新的强化

## 需求分析

有时候界面已经完成了基本的更新，但是有些数据的更新并不及时。
现有的`webhook`只会把所有的内容全部来一遍，但是现在我需要对某些属性进行特定更新.

因此需要增加新的`webhook`

## 基本思路梳理

目前的上传其实就是界面page的更新，但是会把很多属性全部塞进去，可以在这里进行改动。

其实之前有个子问题，需要解决，但是没解决。

- [x] 基本解决，multi-select空的能上传, 但是select不行

processed_data = self._prepare_data(album_data)


## 客户端操作梳理

编辑按钮，

找到想要上传的更新内容，进行更新。

我Notion端只能向服务端传达我需要更新的内容，不能说我要更新这个，我就把这个传递过去，

我想到的一个思路是设置一个`multi select` property, 随后想要更新什么就在里面选择什么

```json
    "Update_selection": {
      "id": "H%5EXV",
      "type": "multi_select",
      "multi_select": [
        {
          "id": "611fa5fc-14b9-4455-b93e-75c860a67d88",
          "name": "Cover_horizontal",
          "color": "orange"
        },
        {
          "id": "34fca6d0-f31c-45c6-9220-fd076503ca72",
          "name": "Cover_square",
          "color": "blue"
        },
        {
          "id": "db002288-85ae-408a-a9eb-43a6240fe1bc",
          "name": "播放",
          "color": "gray"
        },
        {
          "id": "9ea7a7b2-1a85-45dd-a86f-8209fab367a2",
          "name": "追剧",
          "color": "purple"
        }
      ]
    }
```

- [x] 更新需求如下：

  Notion Data source 的全部property为`data\notion_data_source_info.json`, 

  需要实现`NotionService.update_partial_album_data(...)`对任意数据库中的property实现更新，其中property中不包括公式和Fanjiao API中不存在的。

  解决办法是引入`from enum import StrEnum`, 主役要求python3.11+


# Acknowledgement

[zhufree (zhufree)](https://github.com/zhufree)

[首页 Home | 百合Hub](https://baihehub.com/)
