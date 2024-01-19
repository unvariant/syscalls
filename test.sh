ctags \
-o - \
--output-format=json \
--language-force=c \
--kinds-c='+z+p' \
--fields-c='+{properties}' \
-u -R \
'cache/v6.5-rc6/linux/fs'