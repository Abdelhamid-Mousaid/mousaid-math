# Use a base image with TeX Live pre-installed
FROM texlive/texlive:latest

# Install XeLaTeX and other necessary packages
# texlive-xetex is usually included in texlive/texlive:latest, but we can ensure
# other common packages are available.
# Update package lists and install fonts and other utilities for XeLaTeX
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    fontconfig \
    xfonts-utils \
    texlive-lang-french \
    texlive-latex-extra \
    texlive-fonts-extra \
    lmodern \
    fonts-recommended \
    fonts-freefont-otf \
    fonts-noto-cjk \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Command to run XeLaTeX (this will be overridden by the Python script)
CMD ["xelatex"]

