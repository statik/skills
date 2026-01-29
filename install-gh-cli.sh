#!/bin/bash
# Installs GitHub CLI (gh) in Claude Code remote web sessions
# Ported from https://github.com/oikon48/gh-setup-hooks

set -e

LOG_PREFIX="[install-gh-cli]"
LOCAL_BIN="${HOME}/.local/bin"
GH_PATH="${LOCAL_BIN}/gh"
DEFAULT_GH_VERSION="2.83.2"

log() {
    echo "${LOG_PREFIX} $1" >&2
}

update_path() {
    if [ -n "${CLAUDE_ENV_FILE}" ]; then
        echo "export PATH=\"${LOCAL_BIN}:\$PATH\"" >> "${CLAUDE_ENV_FILE}"
        log "PATH persisted to CLAUDE_ENV_FILE"
    fi
}

get_arch() {
    local arch
    arch=$(uname -m)
    case "${arch}" in
        x86_64)
            echo "amd64"
            ;;
        aarch64|arm64)
            echo "arm64"
            ;;
        *)
            echo ""
            ;;
    esac
}

main() {
    # Only run in remote Claude Code environment
    if [ "${CLAUDE_CODE_REMOTE}" != "true" ]; then
        log "Not a remote session, skipping"
        exit 0
    fi

    log "Remote session detected, checking gh CLI..."

    # Check if gh is already available
    if command -v gh &> /dev/null; then
        version=$(gh --version | head -n1)
        log "gh CLI already available: ${version}"
        exit 0
    fi

    # Check if gh exists in local bin
    if [ -x "${GH_PATH}" ]; then
        log "gh found in ${LOCAL_BIN}"
        update_path
        exit 0
    fi

    log "Installing gh CLI to ${LOCAL_BIN}..."

    # Create local bin directory
    mkdir -p "${LOCAL_BIN}"

    # Detect architecture
    arch=$(get_arch)
    if [ -z "${arch}" ]; then
        log "Unsupported architecture: $(uname -m)"
        exit 0
    fi

    gh_version="${GH_SETUP_VERSION:-${DEFAULT_GH_VERSION}}"
    tarball="gh_${gh_version}_linux_${arch}.tar.gz"
    download_url="https://github.com/cli/cli/releases/download/v${gh_version}/${tarball}"
    checksum_url="https://github.com/cli/cli/releases/download/v${gh_version}/gh_${gh_version}_checksums.txt"

    log "Downloading gh v${gh_version} for ${arch}..."

    temp_dir=$(mktemp -d -t gh-setup-XXXXXX)

    cleanup() {
        rm -rf "${temp_dir}"
    }
    trap cleanup EXIT

    # Download tarball
    if ! curl -fsSL --proto '=https' --tlsv1.2 --connect-timeout 5 --max-time 60 \
        "${download_url}" -o "${temp_dir}/${tarball}"; then
        log "Failed to download gh CLI"
        exit 1
    fi

    # Download and verify checksum
    log "Verifying checksum..."
    if curl -fsSL --connect-timeout 5 --max-time 30 \
        "${checksum_url}" -o "${temp_dir}/checksums.txt" 2>/dev/null; then
        if (cd "${temp_dir}" && grep "${tarball}" checksums.txt | sha256sum -c - &>/dev/null); then
            log "Checksum verified"
        else
            log "Failed to verify checksum, skipping verification"
        fi
    else
        log "Failed to download checksums, skipping verification"
    fi

    # Extract
    log "Extracting..."
    tar -xzf "${temp_dir}/${tarball}" -C "${temp_dir}"

    # Move binary
    extracted_bin="${temp_dir}/gh_${gh_version}_linux_${arch}/bin/gh"
    cp "${extracted_bin}" "${GH_PATH}"
    chmod 755 "${GH_PATH}"

    update_path

    version=$("${GH_PATH}" --version | head -n1)
    log "gh CLI installed successfully: ${version}"
}

main "$@"
