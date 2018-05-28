#!/usr/bin/env python
# coding=utf-8


from setuptools import setup,find_packages


setup(
    name="jd_parser_html",
    version = "0.1",
    author = "jkmiao",
    author_email = "miaoweihong@ipin.com",
    packages = find_packages("src"),
    package_dir={"":"src"},
    include_package_data=True,
    description = ("jd_parser of html files with 51job,zhilian,liepin and lagou"),
    install_requires = ["tgrocery","beautifulsoup4","lxml"],
    )
