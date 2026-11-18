from setuptools import setup

PACKAGE = "gridbot_nodes"

setup(
    name=PACKAGE,
    version="0.1.0",
    packages=[PACKAGE],
    data_files=[
        ("share/ament_index/resource_index/packages", [f"resource/{PACKAGE}"]),
        (f"share/{PACKAGE}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    tests_require=["pytest"],
    maintainer="diamondjdev",
    maintainer_email="diamondjdev@users.noreply.github.com",
    description=f"Gridbot ROS package {PACKAGE}",
    license="MIT",
)
