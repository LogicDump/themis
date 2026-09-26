"""Single root contract shared by Themis Core services."""
from __future__ import annotations
import os
from pathlib import Path
import re

import sys

def get_default_hermes_home() -> Path:
    """Resolve the active Hermes home using Hermes' contract or an explicit env value."""
    try:
        from hermes_constants import get_hermes_home
    except ModuleNotFoundError as exc:
        if exc.name != "hermes_constants":
            raise
    else:
        return Path(get_hermes_home()).expanduser().resolve()

    val = os.environ.get("HERMES_HOME")
    if val and val.strip():
        return Path(val).resolve()
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "config.yaml").is_file() or (parent / "hermes-agent").is_dir():
            return parent.resolve()
    raise RuntimeError(
        "HermesHome não pôde ser resolvido pelo contrato oficial; "
        "defina HERMES_HOME explicitamente para execução standalone."
    )


def default_themis_data_root() -> Path:
    """Standalone fallback matching Hermes' per-plugin persistent storage layout."""
    return get_default_hermes_home() / "plugin-data" / "themis"


def _hermes_plugin_data_root() -> Path | None:
    """Use Hermes' official resolver when running inside the Hermes plugin runtime."""
    if is_running_test_context():
        return None
    try:
        from plugins.plugin_storage import plugin_data_dir
    except ModuleNotFoundError as exc:
        if exc.name in {"plugins", "plugins.plugin_storage", "hermes_constants"}:
            return None
        raise
    return Path(plugin_data_dir("themis")).expanduser().resolve()


_CNJ_RE = re.compile(r"^\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}$")


def validate_process_id(process_id: str) -> str:
    value = str(process_id or "").strip()
    if not _CNJ_RE.fullmatch(value):
        raise ValueError("process_id deve ser um CNJ canônico")
    return value


def process_package_dir(process_id: str, root: Path | None = None) -> Path:
    """Return the isolated package directory for one validated CNJ."""
    cnj = validate_process_id(process_id)
    data_root = (root or themis_data_root()).resolve()
    target = (data_root / "processos" / cnj).resolve()
    if not target.is_relative_to((data_root / "processos").resolve()):
        raise ValueError("process package path escapes the data root")
    return target


def process_db_path(process_id: str, root: Path | None = None) -> Path:
    return process_package_dir(process_id, root) / "process.db"


def process_markdown_dir(process_id: str, root: Path | None = None) -> Path:
    return process_package_dir(process_id, root) / "markdown"


def catalog_db_path(root: Path | None = None) -> Path:
    return (root or themis_data_root()).resolve() / "catalog.db"


def workspace_db_path(root: Path | None = None) -> Path:
    """User/workspace preferences stay separate from process discovery and case data."""
    return (root or themis_data_root()).resolve() / "workspace.db"


def is_running_test_context() -> bool:
    """Detecta se o código está sendo executado sob contexto de testes (unittest / pytest)."""
    if "PYTEST_CURRENT_TEST" in os.environ:
        return True
    if os.environ.get("THEMIS_ALLOW_PROD_ROOT_IN_TESTS") == "1":
        return False
    # Checa argumentos de linha de comando
    for arg in sys.argv:
        lower = str(arg).lower()
        if "unittest" in lower or "pytest" in lower:
            return True
    # Checa pilha de execução
    try:
        import inspect
        for frame in inspect.stack():
            fn = str(frame.filename).lower()
            if "unittest" in fn or "pytest" in fn or "\\tests\\" in fn or "/tests/" in fn:
                return True
    except Exception:
        pass
    return False


def themis_data_root() -> Path:
    """Return the canonical per-plugin data root, unless explicitly overridden.

    THEMIS_DATA_ROOT is reserved for explicit overrides, tests, and migrations.
    """
    value = os.environ.get("THEMIS_DATA_ROOT")
    if value and value.strip():
        root = Path(value).resolve()
    else:
        root = (_hermes_plugin_data_root() or default_themis_data_root()).resolve()

    if is_running_test_context():
        try:
            if root == default_themis_data_root().resolve():
                raise RuntimeError(
                    f"INVARIANTE VIOLADA: testes não podem usar o root padrão do Hermes ({default_themis_data_root()})! "
                    "O teste deve configurar THEMIS_DATA_ROOT para um diretório temporário isolado (ex.: tempfile.TemporaryDirectory)."
                )
        except Exception as e:
            if "INVARIANTE VIOLADA" in str(e):
                raise

    return root


def workspace_root() -> Path:
    value = os.environ.get("APP_ROOT") or os.environ.get("WORKSPACE_ROOT")
    if value:
        return Path(value).resolve()
    return themis_data_root()


def state_root() -> Path:
    """Compatibilidade: aponta para themis_data_root."""
    return themis_data_root()


def index_dir() -> Path:
    return themis_data_root() / "index"


def index_db_path() -> Path:
    """Retorna o caminho do banco SQLite principal (themis.db prioritário)."""
    custom = os.environ.get("THEMIS_DB_PATH")
    if custom:
        return Path(custom).resolve()
    primary = index_dir() / "themis.db"
    if primary.is_file():
        return primary.resolve()
    fallback = index_dir() / "juridico.db"
    if fallback.is_file():
        return fallback.resolve()
    return primary.resolve()


def vector_db_path() -> Path:
    """Retorna o caminho do banco SQLite de vetores."""
    custom = os.environ.get("THEMIS_VECTOR_DB_PATH")
    if custom:
        return Path(custom).resolve()
    primary = index_dir() / "themis_vectors.db"
    if primary.is_file():
        return primary.resolve()
    fallback = index_dir() / "juridico_vectors.db"
    if fallback.is_file():
        return fallback.resolve()
    return primary.resolve()


def documents_dir() -> Path:
    """Diretório de documentos content-addressed."""
    return themis_data_root() / "documentos"


def received_dir() -> Path:
    """Diretório de entrada/recebidos de PDFs originais."""
    return themis_data_root() / "recebidos"


def config_dir() -> Path:
    """Diretório de configuração da Themis."""
    return themis_data_root() / "config"


def fontes_config_path() -> Path:
    """Caminho do arquivo fontes.json."""
    return config_dir() / "fontes.json"


def tools_root() -> Path:
    return themis_data_root() / "bin"


def pdfium_helper_path() -> Path:
    """Localiza o binário do helper PDFium no runtime plugin ou data root."""
    env_path = os.environ.get("PDFIUM_HELPER_PATH")
    if env_path and Path(env_path).is_file():
        return Path(env_path).resolve()

    plugin_root = Path(__file__).resolve().parent.parent
    candidates = [
        # Plugin runtime Hermes / source / package bin
        plugin_root / "bin" / "themis-pdf-pdfium.exe",
        plugin_root / "bin" / "juridico-pdf-pdfium.exe",
        # Hermes installation plugin bin
        get_default_hermes_home() / "plugins" / "themis" / "bin" / "themis-pdf-pdfium.exe",
        # Data root bin
        themis_data_root() / "bin" / "themis-pdf-pdfium.exe",
        themis_data_root() / "bin" / "juridico-pdf-pdfium.exe",
    ]
    for cand in candidates:
        if cand.is_file():
            return cand.resolve()
    return candidates[0].resolve()


def models_dir() -> Path:
    """Diretório de modelos locais (ONNX, tokenizers, etc)."""
    custom = os.environ.get("THEMIS_MODELS_DIR")
    if custom:
        return Path(custom).resolve()
    return themis_data_root() / "models"


def embeddinggemma_onnx_model_path() -> Path:
    """Retorna o caminho do modelo ONNX INT8 de EmbeddingGemma."""
    custom = os.environ.get("THEMIS_EMBEDDING_MODEL_PATH")
    if custom and Path(custom).is_file():
        return Path(custom).resolve()

    plugin_root = Path(__file__).resolve().parent.parent
    candidates = [
        models_dir() / "embeddinggemma-300m-onnx" / "model_int8.onnx",
        plugin_root / "models" / "embeddinggemma-300m-onnx" / "model_int8.onnx",
    ]
    for cand in candidates:
        if cand.is_file():
            return cand.resolve()
    return candidates[0].resolve()


def embeddinggemma_tokenizer_path() -> Path:
    """Retorna o caminho do tokenizer.json de EmbeddingGemma."""
    custom = os.environ.get("THEMIS_TOKENIZER_PATH")
    if custom and Path(custom).is_file():
        return Path(custom).resolve()

    plugin_root = Path(__file__).resolve().parent.parent
    candidates = [
        models_dir() / "embeddinggemma-300m-onnx" / "tokenizer.json",
        plugin_root / "models" / "embeddinggemma-300m-onnx" / "tokenizer.json",
    ]
    for cand in candidates:
        if cand.is_file():
            return cand.resolve()
    return candidates[0].resolve()
