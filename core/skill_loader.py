"""
JAQ-AI Skill Loader — skills/ klasöründen SKILL.md dosyalarını yükler.

Kullanım:
    registry = get_registry()
    skill = registry.get("content-repurposing")
    prompt_block = skill.as_prompt_block(include_files=True)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

SKILLS_ROOT = Path(__file__).parent.parent / "skills"


@dataclass
class Skill:
    name: str
    description: str
    instructions: str
    template_files: dict[str, str] = field(default_factory=dict)

    def as_prompt_block(self, include_files: bool = True) -> str:
        block = f"## Aktif Skill: {self.name}\n\n{self.instructions}"
        if include_files and self.template_files:
            block += "\n\n### Platform Şablonları\n"
            for fname, content in self.template_files.items():
                block += f"\n#### {fname}\n{content}\n"
        return block


class SkillRegistry:
    def __init__(self) -> None:
        self._skills: dict[str, Skill] = {}
        self._load_all()

    def _load_all(self) -> None:
        if not SKILLS_ROOT.exists():
            logger.warning(f"skills/ klasörü bulunamadı: {SKILLS_ROOT}")
            return

        for skill_dir in SKILLS_ROOT.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            try:
                skill = self._parse_skill(skill_dir, skill_md)
                self._skills[skill.name] = skill
                logger.info(f"[SkillRegistry] Loaded skill: {skill.name}")
            except Exception as e:
                logger.error(f"Skill yüklenemedi ({skill_dir.name}): {e}")

    def _parse_skill(self, skill_dir: Path, skill_md: Path) -> Skill:
        raw = skill_md.read_text(encoding="utf-8")

        name = skill_dir.name
        description = ""
        instructions = raw

        if raw.startswith("---"):
            parts = raw.split("---", 2)
            if len(parts) >= 3:
                frontmatter = parts[1]
                instructions = parts[2].strip()
                for line in frontmatter.splitlines():
                    if line.startswith("name:"):
                        name = line.split(":", 1)[1].strip()
                    elif line.startswith("description:"):
                        description = line.split(":", 1)[1].strip()

        templates: dict[str, str] = {}
        templates_dir = skill_dir / "templates"
        if templates_dir.exists():
            for tmpl in sorted(templates_dir.glob("*.md")):
                templates[tmpl.stem] = tmpl.read_text(encoding="utf-8")

        return Skill(
            name=name,
            description=description,
            instructions=instructions,
            template_files=templates,
        )

    def get(self, name: str) -> Skill | None:
        return self._skills.get(name)

    def list_skills(self) -> list[dict]:
        return [
            {"name": s.name, "description": s.description}
            for s in self._skills.values()
        ]


_registry: SkillRegistry | None = None


def get_registry() -> SkillRegistry:
    global _registry
    if _registry is None:
        _registry = SkillRegistry()
    return _registry


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    reg = get_registry()
    print("\nAvailable skills:")
    for s in reg.list_skills():
        print(f"- **{s['name']}**: {s['description']}")
