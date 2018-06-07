#!/usr/bin/python
#-*- coding: utf-8 -*-

__author__ = 'Thomas Jay'


import os
import sys
from os.path import basename
from RFC_PDF_Utils import RFCPDFHandler,PDFHandleMode as mode



def main():
    '''从命令行获取rfc pdf文件,并将其目录添加到标签

       每次处理一个pdf文件
    '''
    pdf_path = sys.argv[1]

    pdf_handler = RFCPDFHandler(pdf_path,mode = mode.NEWLY)
    pdf_handler.add_bookmarks_by_get_catalog_from_pdf(pdf_path, page_offset = 0)
    pdf_handler.save2file(os.path.splitext(basename(pdf_path))[0] +'_bookmark_version.pdf')

if __name__ == '__main__':
    main()