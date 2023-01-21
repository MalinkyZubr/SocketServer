import setuptools

long_desc = open("README.md").read()
required = ["pydantic"] # Comma seperated dependent libraries name

setuptools.setup(
    name="SocketServer",
    version="1.0.0", # eg:1.0.0
    author="Michael Ray",
    author_email="m.ray37990@gmail.com",
    license="GNU Public",
    description="Simple homemade TCP server with SSL encryption built on selectors and raw sockets",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MalinkyZubr/SocketServer",
    packages = ['SocketServer'],
    # project_urls is optional
    key_words="TCP Socket Server",
    install_requires=required,
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
)