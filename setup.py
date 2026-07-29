from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        include_package_data=True,
        packages=find_packages(include=["tabs*", "common_widgets*", "app_data*"]),
        py_modules=["main", "rcaide_io", "utilities"],
        package_data={
            "app_data": [
                "images/*",
                "images/powertrain_symbols/*",
                "style_sheets/*",
                "aircraft/*",
            ],
            "": ["VERSION"],
        },
    )
