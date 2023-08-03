#!/usr/bin/env python3

import logging
import os
import subprocess
import sys

def parse_xml_tag(element, tagName, required=False):
    """Helper function to analyse a xml tag."""
    if element.find(tagName) is not None:
        if element.find(tagName).text is not None:
            return element.find(tagName).text
    if required:
        raise Exception(f'Required tag missing: {tagName}')
    return None 

def parse_xml_tag_list(element, tagName):
    """Helper function to analyse a xml tag which can be occure several times."""
    items = list()
    tags = element.findall(tagName)
    for tagName in tags:
        items.append(tagName.text)
    return items

def parse_xml_attrib(element, attrName, required=False, default=None):
    """Helper function to analyse a xml attribute."""
    if attrName in element.attrib:
        return element.attrib[attrName]
    if required:
        raise Exception(f'Required attribute missing: {attrName}')
    return default 

