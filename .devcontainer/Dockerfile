FROM mcr.microsoft.com/devcontainers/base:bookworm AS default
WORKDIR /home/vscode/.devcontainer-build/
COPY ./.devcontainer/install-scripts/ .uv/ ./
ENV GOPATH="/home/vscode/go"
ENV NVM_DIR="/home/vscode/.nvm"
ENV CLOUDSDK_INSTALL_DIR="/home/vscode/.local/gcloud"
ENV PATH="/home/vscode/.local/bin/:/home/vscode/.local/gcloud/google-cloud-sdk/bin:/home/linuxbrew/.linuxbrew/bin:/home/vscode/.local/go/bin/:/home/vscode/.cargo/bin:/home/vscode/go/bin:/home/vscode/.nvm:/github/home/.local/bin/:/github/home/.local/go/bin/:/github/home/.cargo/bin:/github/home/go/bin:/github/home/.nvm:$PATH"

USER root
RUN --mount=type=cache,dst=/root/.cache/ DEBIAN_FRONTEND=noninteractive \
    echo apt-tools && apt-get update && apt-get upgrade -y --no-install-recommends \
    && apt-get install -y --no-install-recommends apt-transport-https \
        ca-certificates gnupg curl pkg-config cmake libssl-dev git expect \
    && mkdir -p /home/vscode/ && chown -R vscode:vscode /home/vscode/ \
    && mkdir -p /home/vscode/.cache && chown -R vscode:vscode /home/vscode/.cache \
    && mkdir -p /github/home/ && chown -R vscode:vscode /github/home/ \
    && mkdir -p /github/home/.cache && chown -R vscode:vscode /github/home/.cache

RUN --mount=type=cache,dst=/home/vscode/.cache/ --mount=type=cache,dst=/github/home/.cache/ mkdir -p /home/vscode/ && chown -R vscode:vscode /home/vscode/ \
    && mkdir -p /home/vscode/.cache && chown -R vscode:vscode /home/vscode/.cache \
    && mkdir -p /github/home/ && chown -R vscode:vscode /github/home/ \
    && mkdir -p /github/home/.cache && chown -R vscode:vscode /github/home/.cache

USER vscode
RUN --mount=type=cache,dst=/home/vscode/.cache/ --mount=type=cache,dst=/github/home/.cache/ DEBIAN_FRONTEND=noninteractive \
    sudo chown -R vscode:vscode /home/vscode/.cache && sudo chown -R vscode:vscode /github/home/.cache \
    && echo uv && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && chmod +x $HOME/.local/bin/uv $HOME/.local/bin/uvx && uv self update && uvx --version \
    && echo python && uv python install --default && python --version \
    && echo brew && /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" && brew --version \
    && echo helm && brew install helm && helm version \
    && echo kubectl && ./install-kubectl.sh && kubectl version --client \
    && echo gh && ./install-gh.sh && gh --version \
    && echo gcloud && ./install-gcloud.sh && gcloud --version \
    && echo npm && ./install-npm.sh \
    && [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" && npm --version \
    && npm cache clean --force \
    && echo just && npm install -g rust-just && just --version \
    && echo commitizen && npm install commitizen -g && cz --help \
    && echo commitlint && npm install -g @commitlint/cli @commitlint/config-conventional && npx commitlint --version \
    && echo pyright && npm install -g pyright && pyright --version \
    && echo repomix && npm install -g repomix && repomix --version \
    && echo claude && npm install -g @anthropic-ai/claude-code && claude --version \
    && expect migrate-install-claude.exp \
    && echo taplo && curl -fsSL https://github.com/tamasfe/taplo/releases/latest/download/taplo-linux-$(uname -m).gz \
    | gzip -d - | install -m 755 /dev/stdin $HOME/.local/bin/taplo && taplo --version \
    && echo lychee && ./install-lychee.sh \
    && chmod +x $HOME/.local/bin/lychee && lychee --version \
    && echo go && ./install-go.sh && go version \
    && echo mcp-language-server && go install github.com/isaacphi/mcp-language-server@latest && mcp-language-server --help \
    && echo glow && go install github.com/charmbracelet/glow@latest && glow --version \
    && echo yamlfmt && go install github.com/google/yamlfmt/cmd/yamlfmt@latest && yamlfmt -version \
    && echo osv-scanner && go install github.com/google/osv-scanner/cmd/osv-scanner@latest && osv-scanner --version \
    && echo DONE

WORKDIR /home/vscode
