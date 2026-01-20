FROM debian AS build

# Install basic dev dependencies
RUN DEBIAN_FRONTEND=noninteractive apt update && apt install -y \
    curl \
    wget \
    git \
    tar \
    gzip \
    bzip2 \
    tcpdump \
    build-essential \
    cmake \
    gcc \
    strace \
    jq \
    xxd \
    python3 \
    python3-pip \
    pipx \
    binwalk \
    iputils-ping \
    gnupg \
    nodejs \
    npm \
    lua5.3 \
    luarocks \
    ruby-full \
    perl \
    ninja-build \
    pkg-config \
    libtool \
    libtool-bin \
    autoconf \
    automake \
    gettext \
    universal-ctags \
    ripgrep \
    fd-find


# Install golang
RUN curl -fsSLo- https://raw.githubusercontent.com/codenoid/install-latest-go-linux/main/install-go.sh | bash

# Install rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    /root/.cargo/bin/rustup component add rust-analyzer rustfmt

# Install typescript
RUN npm install -g typescript

# Install cursor CLI
RUN curl https://cursor.com/install -fsS | bash

RUN mkdir -p /root/.cursor/projects/working && \
    echo '{"trustedAt": "2026-01-20T04:43:49.587Z","workspacePath": "/working"}' > /root/.cursor/projects/working/.workspace-trusted

#COPY 6680.index.js.patch /root/.local/share/cursor-agent/6680.index.js.patch
#RUN cp /root/.local/share/cursor-agent/6680.index.js.patch $(find /root/.local/share/cursor-agent/versions -name '6680.index.js' -type f | head -n 1) && rm /root/.local/share/cursor-agent/6680.index.js.patch

# Set up locales
RUN apt update && apt install -y locales
RUN echo "LC_ALL=en_US.UTF-8" | tee -a /etc/environment && \
    echo "en_US.UTF-8 UTF-8" | tee -a /etc/locale.gen && \
    echo "LANG=en_US.UTF-8" | tee -a /etc/locale.conf && \
    locale-gen en_US.UTF-8 && \
    DEBIAN_FRONTEND=noninteractive dpkg-reconfigure locales && \
    echo "/root/.cargo/bin:/usr/local/go/bin:/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" >> /etc/profile

# Set all bash commands to have a timeout of 5 minutes
RUN echo 'export TIMEOUT=600' >> /root/.bashrc


# Install Python dependancies
COPY requirements.txt .
RUN pip3 install --break-system-packages --upgrade setuptools
RUN pip3 install --no-cache-dir --break-system-packages --ignore-installed -r requirements.txt
RUN pip3 config set global.break-system-packages true


# Clean up home directory
RUN rm -rf /root/*.tar.gz && \
    mkdir /logs

WORKDIR /working

COPY ./entrypoint.sh /entrypoint.sh

CMD ["/bin/sh", "/entrypoint.sh"]

