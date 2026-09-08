(function(global){
  const shared={
    url:null,
    cell:[96,128],
    grid:[12,4],
    foot:[48,120],
    states:{
      idle:[0,4,8,true],
      walk:[4,6,12,true],
      hit:[10,3,12,false],
      recover:[13,3,10,false],
      cheer:[16,4,8,true],
      anticipation:[20,3,10,false],
      attackA:[23,6,12,false],
      attackB:[29,6,12,false],
      finisher:[35,8,12,false],
      deathEntry:[43,5,10,false]
    }
  };
  const entries={};
  for(const side of ['w','b']) for(const type of 'KQRBNP'){
    entries[side+type]={...shared,cell:[...shared.cell],grid:[...shared.grid],
      foot:[...shared.foot],states:{...shared.states}};
  }
  entries.wN.url='assets/pieces/white-knight.png';
  entries.bN.url='assets/pieces/black-knight.png';
  for(const key of ['wN','bN']){
    entries[key].cell=[128,128];
    entries[key].grid=[8,6];
    entries[key].foot=[64,120];
  }
  global.PIECE_SPRITES=entries;
})(globalThis);
