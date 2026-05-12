#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
命令行辩论脚本：无需启动前端，直接输入参数运行比赛。
"""

import asyncio
import sys
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.database import init_db  # noqa: E402
from backend.models import DifficultyLevel  # noqa: E402
from backend.tournament import run_tournament_match  # noqa: E402
from backend.config import AVAILABLE_MODELS, JUDGE_PANEL  # noqa: E402


WINNER_PRO = "proponent"
WINNER_OPP = "opponent"
WINNER_DRAW = "draw"
WINNER_UNKNOWN = "unknown"
DEFAULT_MODEL_ID = "qwen3.5-plus"


def _prompt_text(prompt: str, default: str = "", required: bool = False) -> str:
    while True:
        text = input(f"{prompt}{' [' + default + ']' if default else ''}: ").strip()
        result = text or default
        if required and not result:
            print("该字段不能为空，请重新输入。")
            continue
        return result


def _prompt_int(prompt: str, default: int) -> int:
    while True:
        text = input(f"{prompt} [{default}]: ").strip() or str(default)
        try:
            number = int(text)
            if number <= 0:
                print("请输入大于 0 的整数。")
                continue
            return number
        except ValueError:
            print("请输入整数。")


def _get_available_models() -> List[str]:
    models = [model.strip() for model in AVAILABLE_MODELS.split(",") if model.strip()]
    if not models:
        print(f"未配置 AVAILABLE_MODELS，默认使用模型：{DEFAULT_MODEL_ID}")
        return [DEFAULT_MODEL_ID]
    return models


def _prompt_model(prompt: str, default: str, available_models: List[str]) -> str:
    while True:
        model = _prompt_text(prompt, default=default, required=True)
        if model in available_models:
            return model
        print(f'模型 "{model}" 不在可用列表中，请从上方列表选择。')


async def _run_game(game_index: int, topic: str, proponent: str, opponent: str, rounds: int) -> Dict:
    print(f"\n========== 第 {game_index} 局开始 ==========")
    winner = WINNER_UNKNOWN
    match_id = ""

    async for event in run_tournament_match(
        topic=topic,
        topic_difficulty=DifficultyLevel.MEDIUM,
        prop_model_id=proponent,
        opp_model_id=opponent,
        prop_personality="rational",
        opp_personality="rational",
        rounds=rounds,
        judges=JUDGE_PANEL,
        enabled_tools=[],
        same_model_battle=(proponent == opponent),
        user_id=None,
    ):
        event_type = event.get("type")
        if event_type == "match_init":
            match_id = event.get("match_id", "")
            print(f"Match ID: {match_id}")
        elif event_type == "status":
            print(f"[状态] {event.get('content', '')}")
        elif event_type == "turn_complete":
            turn = event.get("turn", {})
            role = "正方" if turn.get("speaker_role") == "proponent" else "反方"
            round_no = turn.get("round_number", "?")
            content = turn.get("content", "").strip()
            print(f"\n[{role} Round {round_no}]")
            print(content)
        elif event_type == "judge_complete":
            result = event.get("result", {})
            winner = result.get("winner", WINNER_UNKNOWN)
            print(f"\n[裁判结果] winner={winner}")
        elif event_type == "error":
            print(f"\n[错误] {event.get('content', 'unknown error')}")
        elif event_type == "match_end":
            print(f"\n========== 第 {game_index} 局结束 ==========")

    return {"match_id": match_id, "winner": winner}


async def _main() -> None:
    topic = _prompt_text("请输入辩题", default="", required=True)
    available_models = _get_available_models()
    default_model = available_models[0] if available_models else DEFAULT_MODEL_ID

    print("\n当前可用模型：")
    for idx, model in enumerate(available_models, 1):
        print(f"{idx}. {model}")

    proponent = _prompt_model("请输入正方模型 ID", default_model, available_models)
    opponent = _prompt_model("请输入反方模型 ID", default_model, available_models)
    games = _prompt_int("请输入局数", 1)
    rounds_per_game = _prompt_int("请输入每局轮数", 3)

    init_db()

    summary: Dict[str, int] = {
        WINNER_PRO: 0,
        WINNER_OPP: 0,
        WINNER_DRAW: 0,
        WINNER_UNKNOWN: 0,
    }
    for i in range(1, games + 1):
        result = await _run_game(
            game_index=i,
            topic=topic,
            proponent=proponent,
            opponent=opponent,
            rounds=rounds_per_game,
        )
        winner = result.get("winner", WINNER_UNKNOWN)
        if winner not in summary:
            print(f"[警告] 未知胜者类型: {winner}，将计入 unknown")
            winner = WINNER_UNKNOWN
        summary[winner] += 1

    print("\n========== 总结 ==========")
    print(f"辩题: {topic}")
    print(f"正方: {proponent}")
    print(f"反方: {opponent}")
    print(f"总局数: {games}，每局轮数: {rounds_per_game}")
    print(
        f"正方胜: {summary[WINNER_PRO]} | 反方胜: {summary[WINNER_OPP]} | "
        f"平局: {summary[WINNER_DRAW]} | 未知: {summary[WINNER_UNKNOWN]}"
    )


if __name__ == "__main__":
    asyncio.run(_main())
