#!/bin/bash
# Install age encryption tool + AWS CLI v2 into the backup container.
# Extracts age tarball to temp, installs binaries with install(1).
# Requires: curl, unzip, tar
set -eux

AGE_VERSION="${AGE_VERSION:-v1.2.1}"
arch=$(uname -m)

# --- age ---
if [ "$arch" = "x86_64" ]; then
    age_arch="amd64"
elif [ "$arch" = "aarch64" ]; then
    age_arch="arm64"
else
    echo "Unsupported arch: $arch"
    exit 1
fi

age_url="https://github.com/FiloSottile/age/releases/download/${AGE_VERSION}/age-${AGE_VERSION}-linux-${age_arch}.tar.gz"
age_tmp=$(mktemp -d)
curl -fsSL "$age_url" -o "${age_tmp}/age.tar.gz"
tar -xzf "${age_tmp}/age.tar.gz" -C "$age_tmp"
# The tarball extracts into a subdirectory.  Find the age + age-keygen binaries.
age_bin=$(find "$age_tmp" -type f -name age -not -name "*.tar.gz" | head -1)
age_keygen_bin=$(find "$age_tmp" -type f -name age-keygen | head -1)
if [ -z "$age_bin" ] || [ -z "$age_keygen_bin" ]; then
    echo "Could not locate age binaries in extracted tarball"
    find "$age_tmp" -type f
    exit 1
fi
install -m 0755 "$age_bin" /usr/local/bin/age
install -m 0755 "$age_keygen_bin" /usr/local/bin/age-keygen
rm -rf "$age_tmp"

# --- AWS CLI v2 ---
if [ "$arch" = "x86_64" ]; then
    aws_url="https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip"
elif [ "$arch" = "aarch64" ]; then
    aws_url="https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip"
else
    echo "Unsupported arch: $arch"
    exit 1
fi

aws_tmp=$(mktemp -d)
curl -fsSL "$aws_url" -o "${aws_tmp}/awscliv2.zip"
unzip -q "${aws_tmp}/awscliv2.zip" -d "$aws_tmp"
"${aws_tmp}/aws/install"
rm -rf "$aws_tmp"

# Verify tools
age --version
age-keygen --version 2>/dev/null || true
aws --version
