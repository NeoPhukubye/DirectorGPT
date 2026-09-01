"""Casting and Consistency agent for character continuity."""


from director_gpt.agents import BaseAgent
from director_gpt.models.project import ProjectState


class CastingAgent(BaseAgent):
    """Maintains character and environment visual embeddings across scenes."""

    def get_role_description(self) -> str:
        return "Ensures visual consistency of characters and environments across all generated assets"

    def __init__(self, name: str, state: ProjectState, llm_client=None):
        super().__init__(name, state, llm_client=llm_client)

    def process(self, input_data: dict) -> dict:
        """Process script to ensure consistency."""
        mode = input_data.get("mode", "consistency")
        script = input_data.get("script", {})
        characters = script.get("characters", [])
        scenes = script.get("scenes", [])

        self.log(f"Analyzing {len(characters)} characters across {len(scenes)} scenes")

        if mode == "critique":
            return self._critique_script(scenes, characters)

        character_prompts = self._generate_character_prompts(characters)
        environment_prompts = self._generate_environment_prompts(scenes)
        consistency_notes = self._generate_consistency_notes(scenes, characters)

        for char_name in character_prompts:
            self.log(f"Consistency embedding for {char_name}: created")

        return {
            "character_prompts": character_prompts,
            "environment_prompts": environment_prompts,
            "consistency_notes": consistency_notes,
        }

    def _critique_script(self, scenes: list[dict], characters: list[dict]) -> dict:
        """Critique the script for continuity issues."""
        critique_notes = []
        character_appearances = {}

        for scene in scenes:
            for char in scene.get("characters", []):
                character_appearances.setdefault(char, []).append(scene["scene_number"])

        for char_name, scene_numbers in character_appearances.items():
            if len(scene_numbers) > 1:
                critique_notes.append({
                    "type": "character_continuity",
                    "subject": char_name,
                    "scenes": scene_numbers,
                    "note": f"Ensure {char_name} appears visually consistent across scenes {scene_numbers}",
                })

        if not critique_notes:
            critique_notes.append({
                "type": "continuity_check",
                "subject": "all",
                "scenes": [s.get("scene_number") for s in scenes],
                "note": "No major continuity issues detected",
            })

        return {
            "critique_notes": critique_notes,
        }

    def _generate_character_prompts(self, characters: list[dict]) -> dict[str, str]:
        """Generate consistent visual prompts for each character."""
        prompts = {}

        for char in characters:
            name = char.get("name", "Unknown")
            description = char.get("description", "")
            visual_prompt = char.get("visual_prompt", "")

            consistency_prompt = self._build_consistency_prompt(name, description, visual_prompt)
            prompts[name] = consistency_prompt

        return prompts

    def _build_consistency_prompt(self, name: str, description: str, visual_prompt: str) -> str:
        """Build a consistency-preserving visual prompt for a character."""
        features = self._extract_character_features(description)

        prompt_parts = [
            f"character:{name}",
            features.get("age_range", "adult"),
            features.get("gender", ""),
            features.get("build", "average build"),
            features.get("hair", ""),
            features.get("distinctive_features", ""),
            features.get("style", ""),
            visual_prompt,
            "consistent character design, same person across all shots",
            "character reference sheet style, front-facing, neutral expression",
        ]

        return ", ".join(p for p in prompt_parts if p)

    def _extract_character_features(self, description: str) -> dict[str, str]:
        """Extract visual features from character description."""
        features = {}
        desc_lower = description.lower()

        if any(w in desc_lower for w in ["young", "youth", "teen"]):
            features["age_range"] = "young adult, early 20s"
        elif any(w in desc_lower for w in ["old", "elderly", "aged"]):
            features["age_range"] = "elderly, 60s, weathered face"
        else:
            features["age_range"] = "adult, mid 30s"

        if any(w in desc_lower for w in ["woman", "female", "girl", "lady"]):
            features["gender"] = "female"
        elif any(w in desc_lower for w in ["man", "male", "boy", "gentleman"]):
            features["gender"] = "male"

        if any(w in desc_lower for w in ["tall", "lanky"]):
            features["build"] = "tall, lean build"
        elif any(w in desc_lower for w in ["short", "stocky"]):
            features["build"] = "short, stocky build"
        elif any(w in desc_lower for w in ["athletic", "muscular"]):
            features["build"] = "athletic build"

        if any(w in desc_lower for w in ["blonde", "blond"]):
            features["hair"] = "blonde hair"
        elif any(w in desc_lower for w in ["brunette", "brown hair"]):
            features["hair"] = "brown hair"
        elif any(w in desc_lower for w in ["redhead", "red hair"]):
            features["hair"] = "red hair"
        elif any(w in desc_lower for w in ["dark hair", "black hair"]):
            features["hair"] = "dark hair"

        if any(w in desc_lower for w in ["scar", "tattoo", "birthmark", "freckle"]):
            features["distinctive_features"] = description

        return features

    def _generate_environment_prompts(self, scenes: list[dict]) -> dict[str, str]:
        """Generate consistent environment prompts for recurring locations."""
        location_prompts = {}
        seen_locations = {}

        for scene in scenes:
            location = scene.get("location", "")
            env_prompt = scene.get("environment_prompt", "")

            base_location = self._normalize_location(location)

            if base_location in seen_locations:
                if env_prompt and env_prompt != seen_locations[base_location]:
                    self.log(f"Note: Environment variation for {base_location}")
            else:
                seen_locations[base_location] = env_prompt

            location_prompts[location] = self._build_environment_consistency_prompt(
                location, env_prompt
            )

        return location_prompts

    def _normalize_location(self, location: str) -> str:
        """Normalize location string for comparison."""
        return location.split(",")[0].strip().lower()

    def _build_environment_consistency_prompt(self, location: str, env_prompt: str) -> str:
        """Build consistency-preserving environment prompt."""
        prompt_parts = [
            f"location:{location}",
            env_prompt,
            "consistent environment design",
            "same location across all shots",
            "matching lighting conditions, matching props",
            "environment reference, establishing shot perspective",
        ]

        return ", ".join(p for p in prompt_parts if p)

    def _generate_consistency_notes(self, scenes: list[dict], characters: list[dict]) -> list[dict]:
        """Generate notes about continuity concerns."""
        notes = []

        character_appearances = {}
        for scene in scenes:
            for char in scene.get("characters", []):
                if char not in character_appearances:
                    character_appearances[char] = []
                character_appearances[char].append(scene["scene_number"])

        for char_name, scene_numbers in character_appearances.items():
            if len(scene_numbers) > 1:
                notes.append({
                    "type": "character_continuity",
                    "subject": char_name,
                    "scenes": scene_numbers,
                    "note": f"Ensure {char_name} appears visually consistent across scenes {scene_numbers}",
                })

        return notes
