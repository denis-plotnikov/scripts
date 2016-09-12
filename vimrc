set listchars=eol:$,tab:>-,trail:~,extends:>,precedes:<

" first, enable status line always
set laststatus=2
"
" " now set it up to change the status line based on mode
if version >= 700
au InsertEnter * hi StatusLine term=reverse ctermbg=5 gui=undercurl guisp=Magenta
au InsertLeave * hi StatusLine term=reverse ctermfg=0 ctermbg=2 gui=bold,reverse
" search highlighting
endif
"turn on serach highlighting
set hlsearch

:nmap <F2> :ts <c-r>=expand("<cword>")<cr><Enter>
