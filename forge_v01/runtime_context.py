"""Authoritative runtime context that keeps grading, vocab, and validation aligned."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .content_ir_loader import load_content_ir_bundle
from .content_ir_registry import ContentIRRegistry
from .contract_validator import ContractValidator
from .grading_runtime import grade_generated_instance_response, grade_item_response
from .obs_vocab_registry import ObservationVocabularyRegistry


@dataclass
class ForgeRuntimeContext:
    content_ir_registry: ContentIRRegistry
    obs_vocab_registry: ObservationVocabularyRegistry
    contract_validator: ContractValidator

    @classmethod
    def from_bundle(cls, bundle: dict[str, Any]) -> "ForgeRuntimeContext":
        registry = ContentIRRegistry()
        registry.register_bundle(bundle)
        obs_vocab = ObservationVocabularyRegistry()
        obs_vocab.register_bundle(bundle)
        validator = ContractValidator(content_ir_registry=registry)
        return cls(
            content_ir_registry=registry,
            obs_vocab_registry=obs_vocab,
            contract_validator=validator,
        )

    @classmethod
    def from_bundle_path(cls, path: str | Path) -> "ForgeRuntimeContext":
        bundle = load_content_ir_bundle(str(path))
        return cls.from_bundle(bundle)

    def grade_item_response(
        self,
        content_ir_version: str,
        item_id: str,
        raw_response: dict[str, Any],
        runtime_context: dict[str, Any] | None = None,
    ) -> Any:
        return grade_item_response(
            self.content_ir_registry,
            content_ir_version,
            item_id,
            raw_response,
            runtime_context,
        )

    def grade_generated_instance_response(
        self,
        content_ir_version: str,
        generator_id: str,
        generated_instance: dict[str, Any],
        raw_response: dict[str, Any],
        runtime_context: dict[str, Any] | None = None,
    ) -> Any:
        return grade_generated_instance_response(
            self.content_ir_registry,
            content_ir_version,
            generator_id,
            generated_instance,
            raw_response,
            runtime_context,
        )
