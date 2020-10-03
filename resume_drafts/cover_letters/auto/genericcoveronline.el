(TeX-add-style-hook
 "genericcoveronline"
 (lambda ()
   (TeX-add-to-alist 'LaTeX-provided-class-options
                     '(("letter" "12pt")))
   (TeX-run-style-hooks
    "latex2e"
    "letter"
    "letter12"
    "amssymb"
    "amsmath"
    "graphicx"
    "hyperref"))
 :latex)

