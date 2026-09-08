#!/usr/bin/perl
# build-standalone.js 를 그대로 옮긴 것 (이 PC에 Node가 없어서).
# 원본 JS와 같은 순서·같은 치환을 하고, 문자열 replace는 첫 번째만 바꾼다.
use strict; use warnings; use MIME::Base64 qw(encode_base64);

my $SRC   = 'chess.html';
my $SHEET = -e 'sprites-web.png' ? 'sprites-web.png' : 'sprites.png';

sub slurp { my $f=shift; open my $h,'<:raw',$f or die "$f: $!"; local $/; <$h> }
sub spew  { my ($f,$d)=@_; open my $h,'>:raw',$f or die "$f: $!"; print $h $d; close $h }

my $html = slurp($SRC);
my $uri  = 'data:image/png;base64,' . encode_base64(slurp($SHEET), '');

# 1) :root 시작에 시트를 데이터 URI로 꽂는다 (첫 번째 한 곳만)
my $needle = ':root{';
my $at = index($html, $needle);
die "':root{' 를 못 찾음\n" if $at < 0;
substr($html, $at, length($needle)) = qq{:root{--sheet:url("$uri");\n  };

# 2) 파일 경로 참조를 시트 변수로 (모든 곳)
my $n2 = ($html =~ s/\Qbackground-image:url(sprites.png)\E/background-image:var(--sheet)/g);

# 3) 그림 불러오는 IIFE 제거 — 이미 파일 안에 있다
my $n3 = ($html =~ s{\(function loadSheet\(\)\{.*?\}\)\(\);}
                    {SPR=true;   // 그림이 파일 안에 들어있다}s);
die "loadSheet IIFE 를 못 찾음\n" unless $n3;

mkdir 'deploy' unless -d 'deploy';
spew('standalone.html', $html);
spew('deploy/index.html', $html);
my $art = $html; $art =~ s/^<!doctype html>\r?\n//i;
spew('artifact.html', $art);

printf "시트: %s (%dKB)  치환: url %d곳, loadSheet %d곳\n",
  $SHEET, int((-s $SHEET)/1024+.5), $n2, $n3;
printf "결과: standalone.html %dKB · deploy/index.html · artifact.html %dKB\n",
  int(length($html)/1024+.5), int(length($art)/1024+.5);
my ($u) = $html =~ /(data:image\/png;base64,[A-Za-z0-9+\/=]+)/;
printf "CSS 데이터 URI 한도(약 2MB): %s (%d바이트)\n",
  (length($u) < 2000000 ? 'OK' : '초과!'), length($u);
