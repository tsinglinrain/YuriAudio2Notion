# 参数

## 饭角element提取

name
description
horizontal,废弃
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

基本完成, 已经能够完成工作流,

但是, 需要将base url隐藏, achieved

需要将类改成可以更新, achieved

Tag其实也可从简介部分分析, 如纯爱, 古风等. achieved

prompt, 对于诸如"全一季现代纯爱广播剧《有趣》""全一季科幻悬疑百合广播剧《离开与你相遇的世界》""现代纯爱广播剧《帮我拍拍》第一季"等字符串，想要提取每一个的tag，如'全一季""现代""纯爱".需要注意的是，每个字符串"广播剧《"前面内容都是未知的,如何提取呢？

GitHub项目, 中文分词太重, 不合适
直接取吧. achieved

up主也可从简介中提取, achieved

注意, `main`函数没有修改, achieved

main函数以及调试函数, 大量函数重复, 可以用类封装, achieved

正剧的剧集数也可以传入,抓"正剧"

# icon获取方法

1. 打开任意`page`
2. `/`呼出菜单后,键入`emoji`,选择`Emoji`后弹出emoji菜单
3. 选择需要的`emoji`
4. 复制过来🎧(emoji不一样, 不要紧, 上传上去都是一样的)



# Acknowledgement

[zhufree (zhufree)](https://github.com/zhufree)

[首页 Home | 百合Hub](https://baihehub.com/)
