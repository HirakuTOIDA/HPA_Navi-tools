# -*- coding: utf-8 -*-
import sys
import os.path

import SylphideProcessor

if __name__ == "__main__":
    # ログファイルの読み込み
    argvs = sys.argv
    argc = len(argvs)

    if argc != 2:
        print ("Usage: # python {0} filename'".format(argvs[0]))
        quit()

    filename = argvs[1]
    name, ext = os.path.splitext(filename)
    fobj = open(filename, 'rb')

    page = SylphideProcessor.page()
    pagea = SylphideProcessor.pagea()
    pagef = SylphideProcessor.pagef()
    pageh = SylphideProcessor.pageh()
    pageg = SylphideProcessor.pageg()
    pagem = SylphideProcessor.pagem()
    pagen = SylphideProcessor.pagen()
    pageo = SylphideProcessor.pageo()
    pagep = SylphideProcessor.pagep()
    pages = SylphideProcessor.pages()

    try:
        while True:
            h_data = fobj.read(page.size)
            if len(h_data) < page.size:
                break
            if h_data[0] == ord('A'):
                pagea.append(h_data)
            elif h_data[0] == ord('F'):
                pagef.append(h_data)
            elif h_data[0] == ord('G'):
                pageg.append(h_data)
            elif h_data[0] == ord('H'):
                pageh.append(h_data)
            elif h_data[0] == ord('M'):
                pagem.append(h_data)
            elif h_data[0] == ord('N'):
                pagen.append(h_data)
            elif h_data[0] == ord('O'):
                pageo.append(h_data)
            elif h_data[0] == ord('P'):
                pagep.append(h_data)
            elif h_data[0] == ord('S'):
                pages.append(h_data)
    finally:
        fobj.close()
    pagea.raw2phys()
    pagea.save_raw_csv(name + "_A.csv")

    pagef.save_raw_csv(name + "_F.csv")

    pageg.save_raw_ubx(name + "_G.ubx")

    pageh.raw2phys()
    pageh.save_raw_csv(name + "_H.csv")

    pagem.raw2phys()
    pagem.save_raw_csv(name + "_M.csv")

    pagen.raw2phys()
    pagen.save_raw_csv(name + "_N.csv")

    pageo.save_raw_csv(name + "_O.csv")

    pagep.save_raw_csv(name + "_P.csv")

    pages.raw2phys()
    pages.save_raw_csv(name + "_S.csv")

    print('*** Estimated GNSS locking time ***')
#    @todo: ubxデータから求める?
    print('PageA: {0} s'.format(pagea.time_gps_lock()))
    print('PageH: {0} s'.format(pageh.time_gps_lock()))
