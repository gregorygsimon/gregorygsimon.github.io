(TeX-add-style-hook
 "genericcoveronline"
 (lambda ()
   (TeX-run-style-hooks
    "latex2e"
    "letter"
    "letter10"
    "amssymb"
    "amsmath"
    "graphicx"))
 :latex)

