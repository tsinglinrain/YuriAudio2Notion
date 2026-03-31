#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
DescriptionAudioParser 单元测试

测试用例均来源于真实的 Fanjiao 音频描述文本，
覆盖各类职责格式、歌词分割标记及边界情况。
"""

import pytest
from app.core.description_audio_parser import DescriptionAudioParser


# ---------------------------------------------------------------------------
# Fixtures — 来自真实数据的描述文本片段
# ---------------------------------------------------------------------------

# 落音记第一季·主题曲《声声慢》：作词/作曲/编曲/演唱 四职同人，全角斜杠+空格
DESC_SHENGSHENGMAN = (
    '"看遍春夏秋冬与你共白首  哪怕只是黄粱一梦"\n\n'
    "长佩文学，闻人碎语原著，仟金不换工作室出品，饭角APP独播，"
    "古风百合广播剧《落音记》第一季主题曲发布！\n\n"
    "《声声慢》\n"
    "作词 ／作曲／编曲／演唱：水原\n"
    "混音：dB音频工作室\n"
    "出品：仟金不换工作室\n\n"
    "歌词：\n"
    "啊····\n孤月泠 瑟瑟秋风起\n红烛点点照残影\n"
)

# 落音记第二季·主题曲《相思结》：演唱/作词各独行，混音独行
DESC_XIANGSI = (
    '"我祈愿 相守 永不变。"\n\n'
    "《相思结》\n"
    "演唱：纸巾\n"
    "作词/作曲/编曲：水原\n"
    "混音：dB音频工作室\n"
    "统筹：予光惜辰\n\n"
    "歌词：\n"
    "一轮明月 皎皎如霜雪\n你的眉眼 萦绕在 我心间\n"
)

# 冒犯·主题曲《坠入晚烟》：作编曲（同时映射 composer+arranger），分轨混音，演唱/和声合并
DESC_ZHUIRU = (
    "全一季现代百合广播剧《冒犯》主题曲《坠入晚烟》，欢迎收听~\n\n"
    "-STAFF-\n"
    "制作人：牛肉酱\n"
    "演唱/和声：水母\n"
    "作词：沐云汐\n"
    "作编曲：薛由理\n"
    "分轨混音：漫漫\n"
    "字设：一勺酸橙汁\n\n"
    "歌词：\n"
    "许是清晨雏鸟早飞\n阳光格外明媚\n"
)

# 晚潮·主题曲：作曲/演唱 合并，编曲/混音 合并，人名均带 @handle
DESC_WANCHAO = (
    "✨主题曲《晚潮》正式发布✨\n\n"
    "🌊制作组🌊\n"
    "制作人：R\n"
    "作词：路西西\n"
    "作曲/演唱：ZIMA芝麻酱@ZIMA芝麻酱\n"
    "编曲/混音：dB音频工作室@dB音频工作室\n"
    "海报设计：Libby\n\n"
    "【歌词】\n"
    "星光坠落\n月色轻拂\n"
)

# 神龛第二季·主题曲《Shrine》：以 ——————————（全角破折号线）分隔歌词
DESC_SHRINE = (
    "《神龛》广播剧第二季主题曲｜《Shrine》正式发布💿\n\n"
    "制作人：R\n"
    "作词：路西西\n"
    "作曲/演唱：ZIMA芝麻酱@ZIMA芝麻酱\n"
    "混音/编曲：dB音频工作室@dB音频工作室\n"
    "海报设计：Libby\n\n"
    "📅追剧日历📅\n1月7日：18点第一期\n"
    "\n——————————\n"
    "漫无目的地轻描和淡写\n提及往事与未来的契约\n"
)

# 有风伴我的以后·主题曲：以 ——《歌名》歌词—— 分隔
DESC_YOUFENG = (
    "情感曲《有风伴我的以后》正式发布\n\n"
    "演唱：纸巾\n"
    "作词：予光惜辰\n"
    "作曲：水原\n"
    "编曲：dB音频工作室\n"
    "混音：dB音频工作室\n\n"
    "——《有风伴我的以后》歌词——\n"
    "风吹来 你的名字\n落在心上\n"
)

# 非音乐描述（预告/前采）：无任何制作人员信息
DESC_NON_MUSIC = (
    '"局已成，一子落，满盘赢。"\n\n'
    "长佩文学，闻人碎语原著，仟金不换工作室出品，饭角独播，"
    "古风百合广播剧《落音记》第一季预告《解》正式发布！\n\n"
    "预告制作组：\n"
    "原著：闻人碎语\n"
    "策导：予光惜辰\n"
    "配音导演：蔡娜\n"
    "字幕：羿清泽\n"
)


# ---------------------------------------------------------------------------
# 字段提取测试
# ---------------------------------------------------------------------------


class TestSingerExtraction:
    def test_singer_single_line(self):
        p = DescriptionAudioParser(DESC_XIANGSI)
        assert p.singer == ["纸巾"]

    def test_singer_combined_with_lyrics_role(self):
        """演唱/和声：水母 — 只映射演唱，和声不在 _ROLE_MAP 中"""
        p = DescriptionAudioParser(DESC_ZHUIRU)
        assert p.singer == ["水母"]

    def test_singer_combined_with_composer(self):
        """作曲/演唱：ZIMA芝麻酱@ZIMA芝麻酱"""
        p = DescriptionAudioParser(DESC_WANCHAO)
        assert p.singer == ["ZIMA芝麻酱"]

    def test_singer_fullwidth_slash_multi_role(self):
        """作词 ／作曲／编曲／演唱：水原（全角斜杠、带空格）"""
        p = DescriptionAudioParser(DESC_SHENGSHENGMAN)
        assert p.singer == ["水原"]

    def test_singer_from_youfeng(self):
        p = DescriptionAudioParser(DESC_YOUFENG)
        assert p.singer == ["纸巾"]


class TestLyricistExtraction:
    def test_lyricist_standalone(self):
        p = DescriptionAudioParser(DESC_WANCHAO)
        assert p.lyricist == ["路西西"]

    def test_lyricist_combined_roles(self):
        """作词/作曲/编曲：水原"""
        p = DescriptionAudioParser(DESC_XIANGSI)
        assert p.lyricist == ["水原"]

    def test_lyricist_fullwidth_slash(self):
        """作词 ／作曲／编曲／演唱：水原"""
        p = DescriptionAudioParser(DESC_SHENGSHENGMAN)
        assert p.lyricist == ["水原"]

    def test_lyricist_standalone_separate_line(self):
        p = DescriptionAudioParser(DESC_ZHUIRU)
        assert p.lyricist == ["沐云汐"]


class TestComposerExtraction:
    def test_composer_combined_roles(self):
        """作词/作曲/编曲：水原"""
        p = DescriptionAudioParser(DESC_XIANGSI)
        assert p.composer == ["水原"]

    def test_composer_from_zuobianzou(self):
        """作编曲：薛由理 → composer AND arranger"""
        p = DescriptionAudioParser(DESC_ZHUIRU)
        assert p.composer == ["薛由理"]

    def test_composer_combined_with_singer(self):
        """作曲/演唱：ZIMA芝麻酱@ZIMA芝麻酱"""
        p = DescriptionAudioParser(DESC_WANCHAO)
        assert p.composer == ["ZIMA芝麻酱"]


class TestArrangerExtraction:
    def test_arranger_combined_roles(self):
        """作词/作曲/编曲：水原"""
        p = DescriptionAudioParser(DESC_XIANGSI)
        assert p.arranger == ["水原"]

    def test_arranger_from_zuobianzou(self):
        """作编曲：薛由理 → composer AND arranger"""
        p = DescriptionAudioParser(DESC_ZHUIRU)
        assert p.arranger == ["薛由理"]

    def test_arranger_combined_with_mixer(self):
        """编曲/混音：dB音频工作室@dB音频工作室"""
        p = DescriptionAudioParser(DESC_WANCHAO)
        assert p.arranger == ["dB音频工作室"]

    def test_arranger_combined_with_mixer_reversed(self):
        """混音/编曲：dB音频工作室@dB音频工作室（顺序颠倒）"""
        p = DescriptionAudioParser(DESC_SHRINE)
        assert p.arranger == ["dB音频工作室"]


class TestMixerExtraction:
    def test_mixer_standalone(self):
        p = DescriptionAudioParser(DESC_XIANGSI)
        assert p.mixer == ["dB音频工作室"]

    def test_mixer_fenlü_alias(self):
        """分轨混音：漫漫 → mixer"""
        p = DescriptionAudioParser(DESC_ZHUIRU)
        assert p.mixer == ["漫漫"]

    def test_mixer_combined_with_arranger(self):
        """编曲/混音：dB音频工作室@dB音频工作室"""
        p = DescriptionAudioParser(DESC_WANCHAO)
        assert p.mixer == ["dB音频工作室"]

    def test_mixer_combined_reversed(self):
        """混音/编曲：dB音频工作室@dB音频工作室"""
        p = DescriptionAudioParser(DESC_SHRINE)
        assert p.mixer == ["dB音频工作室"]


# ---------------------------------------------------------------------------
# @handle 清理测试
# ---------------------------------------------------------------------------


class TestHandleStripping:
    def test_handle_stripped_from_singer(self):
        p = DescriptionAudioParser(DESC_WANCHAO)
        assert "ZIMA芝麻酱" in p.singer
        assert not any("@" in name for name in p.singer)

    def test_handle_stripped_from_mixer(self):
        p = DescriptionAudioParser(DESC_WANCHAO)
        assert "dB音频工作室" in p.mixer
        assert not any("@" in name for name in p.mixer)

    def test_multiple_handles_in_same_field(self):
        desc = "演唱：清鸢@qingyuan、纸巾@zhijin\n歌词：\n测试\n"
        p = DescriptionAudioParser(desc)
        assert p.singer == ["清鸢", "纸巾"]


# ---------------------------------------------------------------------------
# 多人解析测试
# ---------------------------------------------------------------------------


class TestMultiplePeople:
    def test_multiple_people_with_dunhao(self):
        """演唱：清鸢、纸巾"""
        desc = "演唱：清鸢、纸巾\n作词：水原\n歌词：\n测试歌词\n"
        p = DescriptionAudioParser(desc)
        assert p.singer == ["清鸢", "纸巾"]

    def test_multiple_people_with_fullwidth_comma(self):
        """演唱：清鸢，纸巾"""
        desc = "演唱：清鸢，纸巾\n歌词：\n测试\n"
        p = DescriptionAudioParser(desc)
        assert p.singer == ["清鸢", "纸巾"]

    def test_no_duplicate_when_role_repeated(self):
        """同一职责出现两次时，姓名不应重复"""
        desc = "作词：水原\n作词：水原\n歌词：\n测试\n"
        p = DescriptionAudioParser(desc)
        assert p.lyricist == ["水原"]


# ---------------------------------------------------------------------------
# 歌词分割测试
# ---------------------------------------------------------------------------


class TestLyricsSplitting:
    def test_lyrics_marker_colon(self):
        """歌词：后跟换行"""
        p = DescriptionAudioParser(DESC_SHENGSHENGMAN)
        assert p.lyrics.startswith("啊····")

    def test_lyrics_marker_bracket(self):
        """【歌词】标记"""
        p = DescriptionAudioParser(DESC_WANCHAO)
        assert p.lyrics.startswith("星光坠落")

    def test_lyrics_marker_title_format(self):
        """——《歌名》歌词——标记"""
        p = DescriptionAudioParser(DESC_YOUFENG)
        assert p.lyrics.startswith("风吹来 你的名字")

    def test_lyrics_marker_dash_line(self):
        """——————————（全角破折号分隔线）"""
        p = DescriptionAudioParser(DESC_SHRINE)
        assert p.lyrics.startswith("漫无目的地轻描和淡写")

    def test_no_lyrics_returns_empty_string(self):
        desc = "演唱：纸巾\n作词：水原\n"
        p = DescriptionAudioParser(desc)
        assert p.lyrics == ""

    def test_credits_not_in_lyrics(self):
        """制作信息不应混入歌词中"""
        p = DescriptionAudioParser(DESC_XIANGSI)
        assert "作词" not in p.lyrics
        assert "混音" not in p.lyrics

    def test_lyrics_not_parsed_as_credits(self):
        """歌词内容中若有冒号，不应被误解析为制作信息"""
        desc = "演唱：纸巾\n歌词：\n春风：吹来\n"
        p = DescriptionAudioParser(desc)
        # "春风：吹来" 在歌词区，不应被解析为任何制作字段
        assert p.singer == ["纸巾"]
        assert p.lyricist == []


# ---------------------------------------------------------------------------
# 非音乐描述 / 边界情况
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_non_music_description_all_empty(self):
        """预告、前采等非音乐描述不应提取到任何制作信息"""
        p = DescriptionAudioParser(DESC_NON_MUSIC)
        assert p.singer == []
        assert p.lyricist == []
        assert p.composer == []
        assert p.arranger == []
        assert p.mixer == []
        assert p.lyrics == ""

    def test_empty_description(self):
        p = DescriptionAudioParser("")
        assert p.singer == []
        assert p.lyrics == ""

    def test_no_description_arg(self):
        p = DescriptionAudioParser()
        assert p.singer == []

    def test_unknown_roles_ignored(self):
        """未知职责（如"策导"、"字幕"）不影响已知字段"""
        p = DescriptionAudioParser(DESC_NON_MUSIC)
        assert p.singer == []
        assert p.mixer == []

    def test_zuobianzou_maps_both_composer_and_arranger(self):
        """作编曲 同时映射 composer 和 arranger，且同一人"""
        p = DescriptionAudioParser(DESC_ZHUIRU)
        assert p.composer == ["薛由理"]
        assert p.arranger == ["薛由理"]

    def test_combined_roles_fullwidth_slash_with_spaces(self):
        """全角斜杠且两侧有空格：作词 ／作曲／编曲／演唱：水原"""
        p = DescriptionAudioParser(DESC_SHENGSHENGMAN)
        assert p.lyricist == ["水原"]
        assert p.composer == ["水原"]
        assert p.arranger == ["水原"]
        assert p.singer == ["水原"]


# ---------------------------------------------------------------------------
# format_to_list 工具方法
# ---------------------------------------------------------------------------


class TestFormatToList:
    def test_empty_list(self):
        assert DescriptionAudioParser.format_to_list([]) == []

    def test_single_item(self):
        assert DescriptionAudioParser.format_to_list(["水原"]) == [{"name": "水原"}]

    def test_multiple_items(self):
        result = DescriptionAudioParser.format_to_list(["纸巾", "水原"])
        assert result == [{"name": "纸巾"}, {"name": "水原"}]
