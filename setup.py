from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        include_package_data=True,
        packages=find_packages(),
        py_modules=["main", "rcaide_io", "utilities"],
        package_data={"": ["VERSION", "app_data/**/*"]},
    )
