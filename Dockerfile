ARG EL_VERSION=9
ARG EL_IMAGE=rockylinux
ARG REGISTRY=quay.io
ARG REGISTRY_NAMESPACE=rockylinux

FROM ${REGISTRY}/${REGISTRY_NAMESPACE}/${EL_IMAGE}:${EL_VERSION} AS build

# Enable CRB repository and install build dependencies
RUN dnf upgrade -y && \
    dnf install -y dnf-plugins-core rpm-build rpmdevtools tar gzip tree && \
    dnf config-manager --set-enabled crb && \
    dnf update -y

# Add non-root user for building
RUN useradd -m builder && \
    chown -R builder:builder /home/builder

# Copy the entire context (sources, specs, and build script)
COPY --chown=builder:builder . /home/builder/

# Make sure the build script is executable
RUN chmod +x /home/builder/build-rpm.sh

# Get dependencies for all the spec files
RUN dnf builddep -y /home/builder/SPECS/*.spec && \
    dnf clean all

# Copy consolidated build scripts to /usr/local/bin for easier access
RUN cp -v /home/builder/build-rpm.sh /usr/local/bin/ && \
    chmod +x /usr/local/bin/build-rpm.sh

# Put a marker file to indicate this is a container environment
RUN touch /.containerenv

# Switch to builder user and set working directory
USER builder
WORKDIR /home/builder

# Use the consolidated build script as entrypoint
ENTRYPOINT ["/home/builder/build-rpm.sh"]
