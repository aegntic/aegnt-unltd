"""
AEGNT-UNLTD Self-Evolution Module
Implements the OODA Loop for nightly mutations
"""

import asyncio
import os
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
import subprocess


@dataclass
class InteractionLog:
    timestamp: datetime
    user_input: str
    ai_output: str
    user_action: str  # "accept" or "reject"
    edit_details: Optional[str] = None


@dataclass
class EvolutionRecord:
    version: int
    timestamp: datetime
    trigger_pattern: str
    changes: str
    success: bool


class SelfEvolver:
    """
    The OODA Loop: Nightly Mutation
    1. Log: Track User Accept/Reject
    2. Reflect: Analyze patterns
    3. Evolve: Update system prompt
    4. Commit: Git push
    """

    def __init__(
        self,
        logs_path: str = "./logs",
        system_prompt_path: str = "./system_prompt.md",
        evolution_history_path: str = "./evolution_history.json",
    ):
        self.logs_path = Path(logs_path)
        self.system_prompt_path = Path(system_prompt_path)
        self.evolution_history_path = Path(evolution_history_path)
        self.evolution_history: List[EvolutionRecord] = self._load_history()

    def _load_history(self) -> List[EvolutionRecord]:
        if self.evolution_history_path.exists():
            with open(self.evolution_history_path) as f:
                data = json.load(f)
                return [EvolutionRecord(**r) for r in data]
        return []

    def _save_history(self):
        with open(self.evolution_history_path, "w") as f:
            json.dump(
                [vars(r) for r in self.evolution_history], f, indent=2, default=str
            )

    def log_interaction(
        self,
        user_input: str,
        ai_output: str,
        user_action: str,
        edit_details: Optional[str] = None,
    ):
        """Log each interaction for analysis"""
        self.logs_path.mkdir(exist_ok=True)

        log = InteractionLog(
            timestamp=datetime.now(),
            user_input=user_input,
            ai_output=ai_output,
            user_action=user_action,
            edit_details=edit_details,
        )

        log_file = self.logs_path / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(vars(log), default=str) + "\n")

    async def analyze_daily_logs(self) -> Dict[str, Any]:
        """Analyze logs from the past 24 hours"""
        logs = []
        yesterday = datetime.now() - timedelta(days=1)

        for log_file in self.logs_path.glob("*.jsonl"):
            if log_file.stat().st_mtime > yesterday.timestamp():
                with open(log_file) as f:
                    for line in f:
                        logs.append(json.loads(line))

        # Analyze patterns
        rejects = [l for l in logs if l.get("user_action") == "reject"]
        accepts = [l for l in logs if l.get("user_action") == "accept"]

        patterns = {
            "total_interactions": len(logs),
            "accepts": len(accepts),
            "rejects": len(rejects),
            "rejection_rate": len(rejects) / len(logs) if logs else 0,
            "common_patterns": self._find_patterns(rejects),
        }

        return patterns

    def _find_patterns(self, rejects: List[Dict]) -> List[str]:
        """Find common patterns in rejections"""
        patterns = []

        if not rejects:
            return patterns

        # Simple pattern detection
        reject_texts = " ".join(
            [r.get("user_input", "") + " " + r.get("edit_details", "") for r in rejects]
        )

        if "code" in reject_texts.lower() or "function" in reject_texts.lower():
            patterns.append("code_generation_issues")

        if "too long" in reject_texts.lower() or "verbose" in reject_texts.lower():
            patterns.append("response_too_verbose")

        if "wrong" in reject_texts.lower() or "incorrect" in reject_texts.lower():
            patterns.append("factual_inaccuracy")

        return patterns

    async def evolve(self, patterns: List[str]) -> bool:
        """Generate and apply system prompt improvements"""
        if not patterns:
            return False

        # Read current system prompt
        current_prompt = ""
        if self.system_prompt_path.exists():
            with open(self.system_prompt_path) as f:
                current_prompt = f.read()

        # Generate evolution prompt
        evolution_prompt = f"""Analyze the following failure patterns and rewrite the system prompt to prevent them:

Patterns to fix: {", ".join(patterns)}

Current system prompt:
{current_prompt}

Provide ONLY the improved system prompt. Focus on:
1. Being more concise in responses
2. Being more accurate with code
3. Following user intent more closely

New system prompt:"""

        # In production, this would call an LLM
        # For now, create a simple evolution
        new_version = len(self.evolution_history) + 1

        # Create evolution record
        record = EvolutionRecord(
            version=new_version,
            timestamp=datetime.now(),
            trigger_pattern=", ".join(patterns),
            changes=f"Fixed patterns: {', '.join(patterns)}",
            success=True,
        )

        self.evolution_history.append(record)
        self._save_history()

        # Update system prompt (in production, use LLM output)
        evolved_prompt = (
            current_prompt
            + f"\n\n<!-- EVOLVED v{new_version}: Fixed {', '.join(patterns)} -->"
        )

        with open(self.system_prompt_path, "w") as f:
            f.write(evolved_prompt)

        return True

    async def commit_evolution(self) -> bool:
        """Git commit the evolution"""
        try:
            # Git add
            subprocess.run(
                [
                    "git",
                    "add",
                    str(self.system_prompt_path),
                    str(self.evolution_history_path),
                ],
                cwd=self.logs_path.parent,
                capture_output=True,
            )

            # Git commit
            version = len(self.evolution_history)
            subprocess.run(
                [
                    "git",
                    "commit",
                    "-m",
                    f"chore(self): evolved system prompt v{version}",
                ],
                cwd=self.logs_path.parent,
                capture_output=True,
            )

            return True
        except Exception as e:
            print(f"Git commit failed: {e}")
            return False

    async def run_nightly_mutation(self) -> Dict[str, Any]:
        """Execute the full OODA loop"""
        # 1. Analyze
        patterns = await self.analyze_daily_logs()

        if patterns.get("rejection_rate", 1.0) < 0.15:
            return {"status": "skipped", "reason": "Acceptance rate > 85%"}

        # 2. Evolve
        failure_patterns = patterns.get("common_patterns", [])
        if failure_patterns:
            await self.evolve(failure_patterns)

        # 3. Commit
        commit_success = await self.commit_evolution()

        return {
            "status": "success" if commit_success else "partial",
            "patterns": patterns,
            "evolutions": len(self.evolution_history),
        }


class CronScheduler:
    """Schedule nightly mutations"""

    def __init__(self, evolver: SelfEvolver):
        self.evolver = evolver

    async def run_at_3am(self):
        """Run mutation at 3 AM local time"""
        while True:
            now = datetime.now()
            target = now.replace(hour=3, minute=0, second=0, microsecond=0)

            if now.hour >= 3:
                target += timedelta(days=1)

            wait_seconds = (target - now).total_seconds()
            await asyncio.sleep(wait_seconds)

            # Run evolution
            result = await self.evolver.run_nightly_mutation()
            print(f"Nightly mutation: {result}")
