import sys
from pathlib import Path
import logging

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.append(str(src_path))

from src.services.matchday_initializer import initialize_laliga_matchdays

# Your COMPLETE LaLiga 2024-25 fixture data (ALL 38 matchdays)
LALIGA_2024_25_COMPLETE_FIXTURES = """2279399,2025-08-15,Round 1,Girona,1,Rayo Vallecano,3,,https://r2.thesportsdb.com/images/media/event/thumb/mkqone1751449889.jpg
2279403,2025-08-15,Round 1,Villarreal,2,Real Oviedo,0,,https://r2.thesportsdb.com/images/media/event/thumb/bz4b851751449895.jpg
2279400,2025-08-16,Round 1,Mallorca,0,Barcelona,3,,https://r2.thesportsdb.com/images/media/event/thumb/4skf9w1751449890.jpg
2279394,2025-08-16,Round 1,Deportivo Alavés,2,Levante,1,,https://r2.thesportsdb.com/images/media/event/thumb/5hwveb1751449881.jpg
2279402,2025-08-16,Round 1,Valencia,1,Real Sociedad,1,,https://r2.thesportsdb.com/images/media/event/thumb/9n8qr91751449894.jpg
2279396,2025-08-17,Round 1,Celta Vigo,0,Getafe,2,,https://r2.thesportsdb.com/images/media/event/thumb/klvu4c1751449884.jpg
2279395,2025-08-17,Round 1,Athletic Bilbao,3,Sevilla,2,,https://r2.thesportsdb.com/images/media/event/thumb/63wubw1751449882.jpg
2279398,2025-08-17,Round 1,Espanyol,2,Atlético Madrid,1,,https://r2.thesportsdb.com/images/media/event/thumb/78osue1751449887.jpg
2279397,2025-08-18,Round 1,Elche,1,Real Betis,1,,https://r2.thesportsdb.com/images/media/event/thumb/gxoqss1751449886.jpg
2279401,2025-08-19,Round 1,Real Madrid,1,Osasuna,0,,https://r2.thesportsdb.com/images/media/event/thumb/dtkht11751449892.jpg
2279406,2025-08-22,Round 2,Real Betis,1,Deportivo Alavés,0,,https://r2.thesportsdb.com/images/media/event/thumb/up68kh1751449899.jpg
2279408,2025-08-23,Round 2,Mallorca,1,Celta Vigo,1,,https://r2.thesportsdb.com/images/media/event/thumb/fk2n0h1751449902.jpg
2279405,2025-08-23,Round 2,Atlético Madrid,1,Elche,1,,https://r2.thesportsdb.com/images/media/event/thumb/kxlbue1751449897.jpg
2279407,2025-08-23,Round 2,Levante,2,Barcelona,3,,https://r2.thesportsdb.com/images/media/event/thumb/c7hafa1751449901.jpg
2279409,2025-08-24,Round 2,Osasuna,1,Valencia,0,,https://r2.thesportsdb.com/images/media/event/thumb/wm2i9t1751449903.jpg
2279410,2025-08-24,Round 2,Real Sociedad,2,Espanyol,2,,https://r2.thesportsdb.com/images/media/event/thumb/bmsrr81751449905.jpg
2279413,2025-08-24,Round 2,Villarreal,5,Girona,0,,https://r2.thesportsdb.com/images/media/event/thumb/zbw39s1751449910.jpg
2279411,2025-08-24,Round 2,Real Oviedo,0,Real Madrid,3,,https://r2.thesportsdb.com/images/media/event/thumb/283hm81751449907.jpg
2279404,2025-08-25,Round 2,Athletic Bilbao,1,Rayo Vallecano,0,,https://r2.thesportsdb.com/images/media/event/thumb/hexfd21751449896.jpg
2279412,2025-08-25,Round 2,Sevilla,1,Getafe,2,,https://r2.thesportsdb.com/images/media/event/thumb/s0ljia1751449909.jpg
2279446,2025-08-27,Round 6,Celta Vigo,1,Real Betis,1,,https://r2.thesportsdb.com/images/media/event/thumb/506laf1751449959.jpg
2279417,2025-08-29,Round 3,Elche,2,Levante,0,,https://r2.thesportsdb.com/images/media/event/thumb/px8afz1751449916.jpg
2279423,2025-08-29,Round 3,Valencia,3,Getafe,0,,https://r2.thesportsdb.com/images/media/event/thumb/u8v9wx1751449924.jpg
2279414,2025-08-30,Round 3,Deportivo Alavés,1,Atlético Madrid,1,,https://r2.thesportsdb.com/images/media/event/thumb/zuv9jg1751449912.jpg
2279422,2025-08-30,Round 3,Real Oviedo,1,Real Sociedad,0,,https://r2.thesportsdb.com/images/media/event/thumb/nbc6jn1751449922.jpg
2279419,2025-08-30,Round 3,Girona,0,Sevilla,2,,https://r2.thesportsdb.com/images/media/event/thumb/6loq7w1751449919.jpg
2279421,2025-08-30,Round 3,Real Madrid,2,Mallorca,1,,https://r2.thesportsdb.com/images/media/event/thumb/r7an1e1751449921.jpg
2279416,2025-08-31,Round 3,Celta Vigo,1,Villarreal,1,,https://r2.thesportsdb.com/images/media/event/thumb/gm3hhj1751449914.jpg
2279415,2025-08-31,Round 3,Real Betis,1,Athletic Bilbao,2,,https://r2.thesportsdb.com/images/media/event/thumb/r0bodx1751449913.jpg
2279418,2025-08-31,Round 3,Espanyol,1,Osasuna,0,,https://r2.thesportsdb.com/images/media/event/thumb/qhvk7j1751449917.jpg
2279420,2025-08-31,Round 3,Rayo Vallecano,1,Barcelona,1,,https://r2.thesportsdb.com/images/media/event/thumb/9ojrnm1751449920.jpg
2279433,2025-09-12,Round 4,Sevilla,2,Elche,2,,https://r2.thesportsdb.com/images/media/event/thumb/9f373m1751449940.jpg
2279429,2025-09-13,Round 4,Getafe,2,Real Oviedo,0,,https://r2.thesportsdb.com/images/media/event/thumb/bcjlu81751449934.jpg
2279432,2025-09-13,Round 4,Real Sociedad,1,Real Madrid,2,,https://r2.thesportsdb.com/images/media/event/thumb/2eih4c1751449939.jpg
2279424,2025-09-13,Round 4,Athletic Bilbao,0,Deportivo Alavés,1,,https://r2.thesportsdb.com/images/media/event/thumb/irvwv31751449926.jpg
2279425,2025-09-13,Round 4,Atlético Madrid,2,Villarreal,0,,https://r2.thesportsdb.com/images/media/event/thumb/0nngr71751449928.jpg
2279427,2025-09-14,Round 4,Celta Vigo,1,Girona,1,,https://r2.thesportsdb.com/images/media/event/thumb/b1lo2w1751449931.jpg
2279430,2025-09-14,Round 4,Levante,2,Real Betis,2,,https://r2.thesportsdb.com/images/media/event/thumb/u1mslg1751449936.jpg
2279431,2025-09-14,Round 4,Osasuna,2,Rayo Vallecano,0,,https://r2.thesportsdb.com/images/media/event/thumb/j5123a1751449937.jpg
2279426,2025-09-14,Round 4,Barcelona,6,Valencia,0,,https://r2.thesportsdb.com/images/media/event/thumb/081m561751449929.jpg
2279428,2025-09-15,Round 4,Espanyol,3,Mallorca,2,,https://r2.thesportsdb.com/images/media/event/thumb/mvvbjt1751449933.jpg
2279436,2025-09-19,Round 5,Real Betis,3,Real Sociedad,1,,https://r2.thesportsdb.com/images/media/event/thumb/1pptcq1751449945.jpg
2279438,2025-09-20,Round 5,Girona,0,Levante,4,,https://r2.thesportsdb.com/images/media/event/thumb/a6l8e81751449947.jpg
2279441,2025-09-20,Round 5,Real Madrid,2,Espanyol,0,,https://r2.thesportsdb.com/images/media/event/thumb/brgxcy1751449951.jpg
2279443,2025-09-20,Round 5,Villarreal,2,Osasuna,1,,https://r2.thesportsdb.com/images/media/event/thumb/sr1pxl1751449955.jpg
2279434,2025-09-20,Round 5,Deportivo Alavés,1,Sevilla,2,,https://r2.thesportsdb.com/images/media/event/thumb/u1r08l1751449942.jpg
2279442,2025-09-20,Round 5,Valencia,2,Athletic Bilbao,0,,https://r2.thesportsdb.com/images/media/event/thumb/u8hpgl1751449953.jpg
2279440,2025-09-21,Round 5,Rayo Vallecano,1,Celta Vigo,1,,https://r2.thesportsdb.com/images/media/event/thumb/350xn31751449950.jpg
2279439,2025-09-21,Round 5,Mallorca,1,Atlético Madrid,1,,https://r2.thesportsdb.com/images/media/event/thumb/ksxyu31751449949.jpg
2279437,2025-09-21,Round 5,Elche,1,Real Oviedo,0,,https://r2.thesportsdb.com/images/media/event/thumb/gdprkm1751449946.jpg
2279435,2025-09-21,Round 5,Barcelona,3,Getafe,0,,https://r2.thesportsdb.com/images/media/event/thumb/8bhd4c1751449943.jpg
2279444,2025-09-23,Round 6,Athletic Bilbao,1,Girona,1,,https://r2.thesportsdb.com/images/media/event/thumb/u3s7h41751449956.jpg
2279447,2025-09-23,Round 6,Espanyol,2,Valencia,2,,https://r2.thesportsdb.com/images/media/event/thumb/crwmsf1751449961.jpg
2279449,2025-09-23,Round 6,Levante,1,Real Madrid,4,,https://r2.thesportsdb.com/images/media/event/thumb/wwsnh91751449964.jpg
2279453,2025-09-23,Round 6,Sevilla,1,Villarreal,2,,https://r2.thesportsdb.com/images/media/event/thumb/0jgems1751449969.jpg
2279448,2025-09-24,Round 6,Getafe,1,Deportivo Alavés,1,,https://r2.thesportsdb.com/images/media/event/thumb/b8vngh1751449962.jpg
2279445,2025-09-24,Round 6,Atlético Madrid,3,Rayo Vallecano,2,,https://r2.thesportsdb.com/images/media/event/thumb/0tuw2g1751449958.jpg
2279451,2025-09-24,Round 6,Real Sociedad,1,Mallorca,0,,https://r2.thesportsdb.com/images/media/event/thumb/7xqid41751449966.jpg
2279450,2025-09-25,Round 6,Osasuna,1,Elche,1,,https://r2.thesportsdb.com/images/media/event/thumb/s9e17z1751449965.jpg
2279452,2025-09-25,Round 6,Real Oviedo,1,Barcelona,3,,https://r2.thesportsdb.com/images/media/event/thumb/rsepis1751449968.jpg
2279459,2025-09-26,Round 7,Girona,0,Espanyol,0,,https://r2.thesportsdb.com/images/media/event/thumb/u9h5hn1751449977.jpg
2279458,2025-09-27,Round 7,Getafe,1,Levante,1,,https://r2.thesportsdb.com/images/media/event/thumb/481swq1751449976.jpg
2279454,2025-09-27,Round 7,Atlético Madrid,5,Real Madrid,2,,https://r2.thesportsdb.com/images/media/event/thumb/91y0za1751449970.jpg
2279460,2025-09-27,Round 7,Mallorca,1,Deportivo Alavés,0,,https://r2.thesportsdb.com/images/media/event/thumb/4p4j911751449979.jpg
2279463,2025-09-27,Round 7,Villarreal,1,Athletic Bilbao,0,,https://r2.thesportsdb.com/images/media/event/thumb/89nmrj1751449983.jpg
2279461,2025-09-28,Round 7,Rayo Vallecano,0,Sevilla,1,,https://r2.thesportsdb.com/images/media/event/thumb/qxxig41751449980.jpg
2279457,2025-09-28,Round 7,Elche,2,Celta Vigo,1,,https://r2.thesportsdb.com/images/media/event/thumb/a8krhq1751449974.jpg
2279455,2025-09-28,Round 7,Barcelona,2,Real Sociedad,1,,https://r2.thesportsdb.com/images/media/event/thumb/qedwh31751449972.jpg
2279456,2025-09-28,Round 7,Real Betis,2,Osasuna,0,,https://r2.thesportsdb.com/images/media/event/thumb/w9eun51751449973.jpg
2279462,2025-09-29,Round 7,Valencia,,Real Oviedo,,,https://r2.thesportsdb.com/images/media/event/thumb/nhb69e1751449982.jpg
2279469,2025-10-03,Round 8,Osasuna,,Getafe,,,https://r2.thesportsdb.com/images/media/event/thumb/pqanv81751449991.jpg
2279472,2025-10-04,Round 8,Real Oviedo,,Levante,,,https://r2.thesportsdb.com/images/media/event/thumb/m2tzjh1751449995.jpg
2279468,2025-10-04,Round 8,Girona,,Valencia,,,https://r2.thesportsdb.com/images/media/event/thumb/vh1pm11751449989.jpg
2279465,2025-10-04,Round 8,Athletic Bilbao,,Mallorca,,,https://r2.thesportsdb.com/images/media/event/thumb/dnj3s91751449986.jpg
2279470,2025-10-04,Round 8,Real Madrid,,Villarreal,,,https://r2.thesportsdb.com/images/media/event/thumb/2wor1t1751449992.jpg
2279464,2025-10-05,Round 8,Deportivo Alavés,,Elche,,,https://r2.thesportsdb.com/images/media/event/thumb/nlwa1x1751449984.jpg
2279473,2025-10-05,Round 8,Sevilla,,Barcelona,,,https://r2.thesportsdb.com/images/media/event/thumb/wsxmd11751449996.jpg
2279467,2025-10-05,Round 8,Espanyol,,Real Betis,,,https://r2.thesportsdb.com/images/media/event/thumb/y4dz5x1751449988.jpg
2279471,2025-10-05,Round 8,Real Sociedad,,Rayo Vallecano,,,https://r2.thesportsdb.com/images/media/event/thumb/r5g6941751449993.jpg
2279466,2025-10-05,Round 8,Celta Vigo,,Atlético Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/n1bqgw1751449987.jpg
2279481,2025-10-17,Round 9,Real Oviedo,,Espanyol,,,https://r2.thesportsdb.com/images/media/event/thumb/39x8b51751450008.jpg
2279482,2025-10-18,Round 9,Sevilla,,Mallorca,,,https://r2.thesportsdb.com/images/media/event/thumb/bs1rsw1751450009.jpg
2279476,2025-10-18,Round 9,Barcelona,,Girona,,,https://r2.thesportsdb.com/images/media/event/thumb/4yo1jp1751450001.jpg
2279483,2025-10-18,Round 9,Villarreal,,Real Betis,,,https://r2.thesportsdb.com/images/media/event/thumb/476pjd1751450010.jpg
2279475,2025-10-18,Round 9,Atlético Madrid,,Osasuna,,,https://r2.thesportsdb.com/images/media/event/thumb/qgd84c1751449999.jpg
2279478,2025-10-19,Round 9,Elche,,Athletic Bilbao,,,https://r2.thesportsdb.com/images/media/event/thumb/wcyrus1751450004.jpg
2279477,2025-10-19,Round 9,Celta Vigo,,Real Sociedad,,,https://r2.thesportsdb.com/images/media/event/thumb/9l37an1751450002.jpg
2279480,2025-10-19,Round 9,Levante,,Rayo Vallecano,,,https://r2.thesportsdb.com/images/media/event/thumb/izbkh81751450006.jpg
2279479,2025-10-19,Round 9,Getafe,,Real Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/mgo8p21751450005.jpg
2279474,2025-10-20,Round 9,Deportivo Alavés,,Valencia,,,https://r2.thesportsdb.com/images/media/event/thumb/fsh3ez1751449998.jpg
2279492,2025-10-24,Round 10,Real Sociedad,,Sevilla,,,https://r2.thesportsdb.com/images/media/event/thumb/m3us521751450022.jpg
2279487,2025-10-25,Round 10,Girona,,Real Oviedo,,,https://r2.thesportsdb.com/images/media/event/thumb/8f282e1751450016.jpg
2279486,2025-10-25,Round 10,Espanyol,,Elche,,,https://r2.thesportsdb.com/images/media/event/thumb/m7vljn1751450014.jpg
2279484,2025-10-25,Round 10,Athletic Bilbao,,Getafe,,,https://r2.thesportsdb.com/images/media/event/thumb/tnp3001751450012.jpg
2279493,2025-10-25,Round 10,Valencia,,Villarreal,,,https://r2.thesportsdb.com/images/media/event/thumb/2u4vq11751450024.jpg
2279488,2025-10-26,Round 10,Mallorca,,Levante,,,https://r2.thesportsdb.com/images/media/event/thumb/llk2ur1751450017.jpg
2279491,2025-10-26,Round 10,Real Madrid,,Barcelona,,,https://r2.thesportsdb.com/images/media/event/thumb/rxho931751450021.jpg
2279489,2025-10-26,Round 10,Osasuna,,Celta Vigo,,,https://r2.thesportsdb.com/images/media/event/thumb/ow7a8f1751450018.jpg
2279490,2025-10-26,Round 10,Rayo Vallecano,,Deportivo Alavés,,,https://r2.thesportsdb.com/images/media/event/thumb/cr2uvm1751450020.jpg
2279485,2025-10-27,Round 10,Real Betis,,Atlético Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/k1ars91751450013.jpg
2279494,2025-11-02,Round 11,Deportivo Alavés,,Espanyol,,,https://r2.thesportsdb.com/images/media/event/thumb/uvmdce1751450025.jpg
2279495,2025-11-02,Round 11,Atlético Madrid,,Sevilla,,,https://r2.thesportsdb.com/images/media/event/thumb/bt79q51751450027.jpg
2279496,2025-11-02,Round 11,Barcelona,,Elche,,,https://r2.thesportsdb.com/images/media/event/thumb/03yac21751450028.jpg
2279497,2025-11-02,Round 11,Real Betis,,Mallorca,,,https://r2.thesportsdb.com/images/media/event/thumb/v2odz31751450029.jpg
2279498,2025-11-02,Round 11,Getafe,,Girona,,,https://r2.thesportsdb.com/images/media/event/thumb/11aiwz1751450031.jpg
2279499,2025-11-02,Round 11,Levante,,Celta Vigo,,,https://r2.thesportsdb.com/images/media/event/thumb/7xj4jf1751450033.jpg
2279500,2025-11-02,Round 11,Real Madrid,,Valencia,,,https://r2.thesportsdb.com/images/media/event/thumb/yjhnol1751450034.jpg
2279501,2025-11-02,Round 11,Real Sociedad,,Athletic Bilbao,,,https://r2.thesportsdb.com/images/media/event/thumb/zl1vau1751450035.jpg
2279502,2025-11-02,Round 11,Real Oviedo,,Osasuna,,,https://r2.thesportsdb.com/images/media/event/thumb/piz49d1751450037.jpg
2279503,2025-11-02,Round 11,Villarreal,,Rayo Vallecano,,,https://r2.thesportsdb.com/images/media/event/thumb/wguqta1751450038.jpg
2279504,2025-11-09,Round 12,Athletic Bilbao,,Real Oviedo,,,https://r2.thesportsdb.com/images/media/event/thumb/n5ph0e1751450040.jpg
2279505,2025-11-09,Round 12,Atlético Madrid,,Levante,,,https://r2.thesportsdb.com/images/media/event/thumb/s8yjq71751450041.jpg
2279506,2025-11-09,Round 12,Celta Vigo,,Barcelona,,,https://r2.thesportsdb.com/images/media/event/thumb/kf9h0i1751450043.jpg
2279507,2025-11-09,Round 12,Elche,,Real Sociedad,,,https://r2.thesportsdb.com/images/media/event/thumb/dy58yj1751450044.jpg
2279508,2025-11-09,Round 12,Espanyol,,Villarreal,,,https://r2.thesportsdb.com/images/media/event/thumb/j45tcs1751450045.jpg
2279509,2025-11-09,Round 12,Girona,,Deportivo Alavés,,,https://r2.thesportsdb.com/images/media/event/thumb/0s26lh1751450047.jpg
2279510,2025-11-09,Round 12,Mallorca,,Getafe,,,https://r2.thesportsdb.com/images/media/event/thumb/k1rxv11751450048.jpg
2279511,2025-11-09,Round 12,Rayo Vallecano,,Real Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/uytp351751450050.jpg
2279512,2025-11-09,Round 12,Sevilla,,Osasuna,,,https://r2.thesportsdb.com/images/media/event/thumb/olgkon1751450051.jpg
2279513,2025-11-09,Round 12,Valencia,,Real Betis,,,https://r2.thesportsdb.com/images/media/event/thumb/u5seku1751450053.jpg
2279514,2025-11-23,Round 13,Deportivo Alavés,,Celta Vigo,,,https://r2.thesportsdb.com/images/media/event/thumb/vgvngo1751450054.jpg
2279515,2025-11-23,Round 13,Barcelona,,Athletic Bilbao,,,https://r2.thesportsdb.com/images/media/event/thumb/d6lsvx1751450056.jpg
2279516,2025-11-23,Round 13,Real Betis,,Girona,,,https://r2.thesportsdb.com/images/media/event/thumb/0518p91751450058.jpg
2279517,2025-11-23,Round 13,Elche,,Real Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/8u7os51751450059.jpg
2279518,2025-11-23,Round 13,Espanyol,,Sevilla,,,https://r2.thesportsdb.com/images/media/event/thumb/cjoc5w1751450060.jpg
2279519,2025-11-23,Round 13,Getafe,,Atlético Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/ggfc031751450062.jpg
2279520,2025-11-23,Round 13,Osasuna,,Real Sociedad,,,https://r2.thesportsdb.com/images/media/event/thumb/0dj3cc1751450064.jpg
2279521,2025-11-23,Round 13,Real Oviedo,,Rayo Vallecano,,,https://r2.thesportsdb.com/images/media/event/thumb/u6bv7n1751450065.jpg
2279522,2025-11-23,Round 13,Valencia,,Levante,,,https://r2.thesportsdb.com/images/media/event/thumb/2ds37l1751450066.jpg
2279523,2025-11-23,Round 13,Villarreal,,Mallorca,,,https://r2.thesportsdb.com/images/media/event/thumb/rhxa7h1751450068.jpg
2279524,2025-11-30,Round 14,Atlético Madrid,,Real Oviedo,,,https://r2.thesportsdb.com/images/media/event/thumb/eip8w31751450070.jpg
2279525,2025-11-30,Round 14,Barcelona,,Deportivo Alavés,,,https://r2.thesportsdb.com/images/media/event/thumb/1fqvrz1751450071.jpg
2279526,2025-11-30,Round 14,Celta Vigo,,Espanyol,,,https://r2.thesportsdb.com/images/media/event/thumb/g3gsci1751450072.jpg
2279527,2025-11-30,Round 14,Getafe,,Elche,,,https://r2.thesportsdb.com/images/media/event/thumb/1gxow01751450073.jpg
2279528,2025-11-30,Round 14,Girona,,Real Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/wq9gw01751450075.jpg
2279529,2025-11-30,Round 14,Levante,,Athletic Bilbao,,,https://r2.thesportsdb.com/images/media/event/thumb/f82ulw1751450076.jpg
2279530,2025-11-30,Round 14,Mallorca,,Osasuna,,,https://r2.thesportsdb.com/images/media/event/thumb/fqaoi21751450078.jpg
2279531,2025-11-30,Round 14,Rayo Vallecano,,Valencia,,,https://r2.thesportsdb.com/images/media/event/thumb/kcc4691751450079.jpg
2279532,2025-11-30,Round 14,Real Sociedad,,Villarreal,,,https://r2.thesportsdb.com/images/media/event/thumb/k2do7d1751450080.jpg
2279533,2025-11-30,Round 14,Sevilla,,Real Betis,,,https://r2.thesportsdb.com/images/media/event/thumb/w22msa1751450082.jpg
2279534,2025-12-07,Round 15,Deportivo Alavés,,Real Sociedad,,,https://r2.thesportsdb.com/images/media/event/thumb/alq9ff1751450083.jpg
2279535,2025-12-07,Round 15,Athletic Bilbao,,Atlético Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/6ikzfl1751450084.jpg
2279536,2025-12-07,Round 15,Real Betis,,Barcelona,,,https://r2.thesportsdb.com/images/media/event/thumb/oibb0b1751450086.jpg
2279537,2025-12-07,Round 15,Elche,,Girona,,,https://r2.thesportsdb.com/images/media/event/thumb/p3dfe51751450087.jpg
2279538,2025-12-07,Round 15,Espanyol,,Rayo Vallecano,,,https://r2.thesportsdb.com/images/media/event/thumb/podv0p1751450088.jpg
2279539,2025-12-07,Round 15,Osasuna,,Levante,,,https://r2.thesportsdb.com/images/media/event/thumb/ethazw1751450090.jpg
2279540,2025-12-07,Round 15,Real Madrid,,Celta Vigo,,,https://r2.thesportsdb.com/images/media/event/thumb/gclyfh1751450091.jpg
2279541,2025-12-07,Round 15,Real Oviedo,,Mallorca,,,https://r2.thesportsdb.com/images/media/event/thumb/eew5741751450092.jpg
2279542,2025-12-07,Round 15,Valencia,,Sevilla,,,https://r2.thesportsdb.com/images/media/event/thumb/0oz54a1751450094.jpg
2279543,2025-12-07,Round 15,Villarreal,,Getafe,,,https://r2.thesportsdb.com/images/media/event/thumb/epem7p1751450096.jpg
2279544,2025-12-14,Round 16,Deportivo Alavés,,Real Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/i8li6j1751450097.jpg
2279545,2025-12-14,Round 16,Atlético Madrid,,Valencia,,,https://r2.thesportsdb.com/images/media/event/thumb/ck7m501751450098.jpg
2279546,2025-12-14,Round 16,Barcelona,,Osasuna,,,https://r2.thesportsdb.com/images/media/event/thumb/wc3ela1751450100.jpg
2279547,2025-12-14,Round 16,Celta Vigo,,Athletic Bilbao,,,https://r2.thesportsdb.com/images/media/event/thumb/69zir51751450101.jpg
2279548,2025-12-14,Round 16,Getafe,,Espanyol,,,https://r2.thesportsdb.com/images/media/event/thumb/44t0mg1751450102.jpg
2279549,2025-12-14,Round 16,Levante,,Villarreal,,,https://r2.thesportsdb.com/images/media/event/thumb/pwfz7v1751450103.jpg
2279550,2025-12-14,Round 16,Mallorca,,Elche,,,https://r2.thesportsdb.com/images/media/event/thumb/upwll31751450105.jpg
2279551,2025-12-14,Round 16,Rayo Vallecano,,Real Betis,,,https://r2.thesportsdb.com/images/media/event/thumb/5239ta1751450106.jpg
2279552,2025-12-14,Round 16,Real Sociedad,,Girona,,,https://r2.thesportsdb.com/images/media/event/thumb/tv7hmp1751450108.jpg
2279553,2025-12-14,Round 16,Sevilla,,Real Oviedo,,,https://r2.thesportsdb.com/images/media/event/thumb/b5w7j81751450109.jpg
2279554,2025-12-21,Round 17,Athletic Bilbao,,Espanyol,,,https://r2.thesportsdb.com/images/media/event/thumb/4ffh4h1751450110.jpg
2279555,2025-12-21,Round 17,Real Betis,,Getafe,,,https://r2.thesportsdb.com/images/media/event/thumb/427no91751450112.jpg
2279556,2025-12-21,Round 17,Elche,,Rayo Vallecano,,,https://r2.thesportsdb.com/images/media/event/thumb/wteian1751450113.jpg
2279557,2025-12-21,Round 17,Girona,,Atlético Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/2794nw1751450115.jpg
2279558,2025-12-21,Round 17,Levante,,Real Sociedad,,,https://r2.thesportsdb.com/images/media/event/thumb/5nx0xo1751450117.jpg
2279559,2025-12-21,Round 17,Osasuna,,Deportivo Alavés,,,https://r2.thesportsdb.com/images/media/event/thumb/par8o31751450118.jpg
2279560,2025-12-21,Round 17,Real Madrid,,Sevilla,,,https://r2.thesportsdb.com/images/media/event/thumb/eh3txd1751450120.jpg
2279561,2025-12-21,Round 17,Real Oviedo,,Celta Vigo,,,https://r2.thesportsdb.com/images/media/event/thumb/msycja1751450121.jpg
2279562,2025-12-21,Round 17,Valencia,,Mallorca,,,https://r2.thesportsdb.com/images/media/event/thumb/oier2v1751450123.jpg
2279563,2025-12-21,Round 17,Villarreal,,Barcelona,,,https://r2.thesportsdb.com/images/media/event/thumb/30mu2m1751450124.jpg
2279564,2026-01-04,Round 18,Deportivo Alavés,,Real Oviedo,,,https://r2.thesportsdb.com/images/media/event/thumb/rc451e1751450125.jpg
2279565,2026-01-04,Round 18,Celta Vigo,,Valencia,,,https://r2.thesportsdb.com/images/media/event/thumb/0uzhpm1751450127.jpg
2279566,2026-01-04,Round 18,Elche,,Villarreal,,,https://r2.thesportsdb.com/images/media/event/thumb/g7daw51751450129.jpg
2279567,2026-01-04,Round 18,Espanyol,,Barcelona,,,https://r2.thesportsdb.com/images/media/event/thumb/rb9jse1751450130.jpg
2279568,2026-01-04,Round 18,Mallorca,,Girona,,,https://r2.thesportsdb.com/images/media/event/thumb/qiv0q41751450132.jpg
2279569,2026-01-04,Round 18,Osasuna,,Athletic Bilbao,,,https://r2.thesportsdb.com/images/media/event/thumb/zv914t1751450133.jpg
2279570,2026-01-04,Round 18,Rayo Vallecano,,Getafe,,,https://r2.thesportsdb.com/images/media/event/thumb/r91op81751450135.jpg
2279571,2026-01-04,Round 18,Real Madrid,,Real Betis,,,https://r2.thesportsdb.com/images/media/event/thumb/yjhu1d1751450136.jpg
2279572,2026-01-04,Round 18,Real Sociedad,,Atlético Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/r93pzj1751450137.jpg
2279573,2026-01-04,Round 18,Sevilla,,Levante,,,https://r2.thesportsdb.com/images/media/event/thumb/8xuzfg1751450139.jpg
2279574,2026-01-11,Round 19,Athletic Bilbao,,Real Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/l5g9h11751450140.jpg
2279575,2026-01-11,Round 19,Barcelona,,Atlético Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/qqbtr61751450142.jpg
2279576,2026-01-11,Round 19,Getafe,,Real Sociedad,,,https://r2.thesportsdb.com/images/media/event/thumb/8lcen71751450143.jpg
2279577,2026-01-11,Round 19,Girona,,Osasuna,,,https://r2.thesportsdb.com/images/media/event/thumb/popbjc1751450144.jpg
2279578,2026-01-11,Round 19,Levante,,Espanyol,,,https://r2.thesportsdb.com/images/media/event/thumb/ux75l81751450146.jpg
2279579,2026-01-11,Round 19,Rayo Vallecano,,Mallorca,,,https://r2.thesportsdb.com/images/media/event/thumb/sbxxgu1751450147.jpg
2279580,2026-01-11,Round 19,Real Oviedo,,Real Betis,,,https://r2.thesportsdb.com/images/media/event/thumb/rzv20f1751450149.jpg
2279581,2026-01-11,Round 19,Sevilla,,Celta Vigo,,,https://r2.thesportsdb.com/images/media/event/thumb/amixrz1751450150.jpg
2279582,2026-01-11,Round 19,Valencia,,Elche,,,https://r2.thesportsdb.com/images/media/event/thumb/kbalzo1751450151.jpg
2279583,2026-01-11,Round 19,Villarreal,,Deportivo Alavés,,,https://r2.thesportsdb.com/images/media/event/thumb/493gc81751450153.jpg
2279584,2026-01-18,Round 20,Atlético Madrid,,Deportivo Alavés,,,https://r2.thesportsdb.com/images/media/event/thumb/yns1i41751450154.jpg
2279585,2026-01-18,Round 20,Real Betis,,Villarreal,,,https://r2.thesportsdb.com/images/media/event/thumb/ivjn671751450156.jpg
2279586,2026-01-18,Round 20,Celta Vigo,,Rayo Vallecano,,,https://r2.thesportsdb.com/images/media/event/thumb/fst6mu1751450157.jpg
2279587,2026-01-18,Round 20,Elche,,Sevilla,,,https://r2.thesportsdb.com/images/media/event/thumb/2sssct1751450159.jpg
2279588,2026-01-18,Round 20,Espanyol,,Girona,,,https://r2.thesportsdb.com/images/media/event/thumb/mv0ajm1751450160.jpg
2279589,2026-01-18,Round 20,Getafe,,Valencia,,,https://r2.thesportsdb.com/images/media/event/thumb/6hz3611751450161.jpg
2279590,2026-01-18,Round 20,Mallorca,,Athletic Bilbao,,,https://r2.thesportsdb.com/images/media/event/thumb/mhfigg1751450163.jpg
2279591,2026-01-18,Round 20,Osasuna,,Real Oviedo,,,https://r2.thesportsdb.com/images/media/event/thumb/rw389k1751450164.jpg
2279592,2026-01-18,Round 20,Real Madrid,,Levante,,,https://r2.thesportsdb.com/images/media/event/thumb/ah6wko1751450166.jpg
2279593,2026-01-18,Round 20,Real Sociedad,,Barcelona,,,https://r2.thesportsdb.com/images/media/event/thumb/nklz5k1751450167.jpg
2279594,2026-01-25,Round 21,Deportivo Alavés,,Real Betis,,,https://r2.thesportsdb.com/images/media/event/thumb/vpjca71751450168.jpg
2279595,2026-01-25,Round 21,Atlético Madrid,,Mallorca,,,https://r2.thesportsdb.com/images/media/event/thumb/ztzglr1751450170.jpg
2279596,2026-01-25,Round 21,Barcelona,,Real Oviedo,,,https://r2.thesportsdb.com/images/media/event/thumb/3lgex51751450172.jpg
2279597,2026-01-25,Round 21,Girona,,Getafe,,,https://r2.thesportsdb.com/images/media/event/thumb/tuzycb1751450173.jpg
2279598,2026-01-25,Round 21,Levante,,Elche,,,https://r2.thesportsdb.com/images/media/event/thumb/x3wyo61751450174.jpg
2279599,2026-01-25,Round 21,Rayo Vallecano,,Osasuna,,,https://r2.thesportsdb.com/images/media/event/thumb/xgkw2c1751450176.jpg
2279600,2026-01-25,Round 21,Real Sociedad,,Celta Vigo,,,https://r2.thesportsdb.com/images/media/event/thumb/5q3ln01751450177.jpg
2279601,2026-01-25,Round 21,Sevilla,,Athletic Bilbao,,,https://r2.thesportsdb.com/images/media/event/thumb/eudq8g1751450179.jpg
2279602,2026-01-25,Round 21,Valencia,,Espanyol,,,https://r2.thesportsdb.com/images/media/event/thumb/2ix42l1751450180.jpg
2279603,2026-01-25,Round 21,Villarreal,,Real Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/s5vlp21751450182.jpg
2279604,2026-02-01,Round 22,Athletic Bilbao,,Real Sociedad,,,https://r2.thesportsdb.com/images/media/event/thumb/qzdpp61751450183.jpg
2279605,2026-02-01,Round 22,Real Betis,,Valencia,,,https://r2.thesportsdb.com/images/media/event/thumb/o28cim1751450185.jpg
2279606,2026-02-01,Round 22,Elche,,Barcelona,,,https://r2.thesportsdb.com/images/media/event/thumb/b7ml9y1751450186.jpg
2279607,2026-02-01,Round 22,Espanyol,,Deportivo Alavés,,,https://r2.thesportsdb.com/images/media/event/thumb/6h7pz41751450188.jpg
2279608,2026-02-01,Round 22,Getafe,,Celta Vigo,,,https://r2.thesportsdb.com/images/media/event/thumb/o493711751450189.jpg
2279609,2026-02-01,Round 22,Levante,,Atlético Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/8tibh21751450191.jpg
2279610,2026-02-01,Round 22,Mallorca,,Sevilla,,,https://r2.thesportsdb.com/images/media/event/thumb/wxmtzn1751450192.jpg
2279611,2026-02-01,Round 22,Osasuna,,Villarreal,,,https://r2.thesportsdb.com/images/media/event/thumb/acgnju1751450194.jpg
2279612,2026-02-01,Round 22,Real Madrid,,Rayo Vallecano,,,https://r2.thesportsdb.com/images/media/event/thumb/ja1zsk1751450195.jpg
2279613,2026-02-01,Round 22,Real Oviedo,,Girona,,,https://r2.thesportsdb.com/images/media/event/thumb/enmkps1751450197.jpg
2279614,2026-02-08,Round 23,Deportivo Alavés,,Getafe,,,https://r2.thesportsdb.com/images/media/event/thumb/03lmv21751450198.jpg
2279615,2026-02-08,Round 23,Athletic Bilbao,,Levante,,,https://r2.thesportsdb.com/images/media/event/thumb/l0ey0a1751450199.jpg
2279616,2026-02-08,Round 23,Atlético Madrid,,Real Betis,,,https://r2.thesportsdb.com/images/media/event/thumb/ggaopo1751450201.jpg
2279617,2026-02-08,Round 23,Barcelona,,Mallorca,,,https://r2.thesportsdb.com/images/media/event/thumb/oa15hs1751450202.jpg
2279618,2026-02-08,Round 23,Celta Vigo,,Osasuna,,,https://r2.thesportsdb.com/images/media/event/thumb/l9adsh1751450204.jpg
2279619,2026-02-08,Round 23,Rayo Vallecano,,Real Oviedo,,,https://r2.thesportsdb.com/images/media/event/thumb/n4851s1751450205.jpg
2279620,2026-02-08,Round 23,Real Sociedad,,Elche,,,https://r2.thesportsdb.com/images/media/event/thumb/pq0t0s1751450207.jpg
2279621,2026-02-08,Round 23,Sevilla,,Girona,,,https://r2.thesportsdb.com/images/media/event/thumb/jx7oqh1751450208.jpg
2279622,2026-02-08,Round 23,Valencia,,Real Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/l17ryd1751450210.jpg
2279623,2026-02-08,Round 23,Villarreal,,Espanyol,,,https://r2.thesportsdb.com/images/media/event/thumb/h4o6791751450212.jpg
2279624,2026-02-15,Round 24,Elche,,Osasuna,,,https://r2.thesportsdb.com/images/media/event/thumb/mq44r21751450213.jpg
2279625,2026-02-15,Round 24,Espanyol,,Celta Vigo,,,https://r2.thesportsdb.com/images/media/event/thumb/tp1jhg1751450214.jpg
2279626,2026-02-15,Round 24,Getafe,,Villarreal,,,https://r2.thesportsdb.com/images/media/event/thumb/f3njao1751450216.jpg
2279627,2026-02-15,Round 24,Girona,,Barcelona,,,https://r2.thesportsdb.com/images/media/event/thumb/2lc9yu1751450217.jpg
2279628,2026-02-15,Round 24,Levante,,Valencia,,,https://r2.thesportsdb.com/images/media/event/thumb/q611cy1751450219.jpg
2279629,2026-02-15,Round 24,Mallorca,,Real Betis,,,https://r2.thesportsdb.com/images/media/event/thumb/zi78pn1751450220.jpg
2279630,2026-02-15,Round 24,Rayo Vallecano,,Atlético Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/x8ho731751450222.jpg
2279631,2026-02-15,Round 24,Real Madrid,,Real Sociedad,,,https://r2.thesportsdb.com/images/media/event/thumb/gwgqdu1751450224.jpg
2279632,2026-02-15,Round 24,Real Oviedo,,Athletic Bilbao,,,https://r2.thesportsdb.com/images/media/event/thumb/o3ndrr1751450225.jpg
2279633,2026-02-15,Round 24,Sevilla,,Deportivo Alavés,,,https://r2.thesportsdb.com/images/media/event/thumb/atr3bo1751450227.jpg
2279634,2026-02-22,Round 25,Deportivo Alavés,,Girona,,,https://r2.thesportsdb.com/images/media/event/thumb/zf7g6g1751450229.jpg
2279635,2026-02-22,Round 25,Athletic Bilbao,,Elche,,,https://r2.thesportsdb.com/images/media/event/thumb/rt05de1751450230.jpg
2279636,2026-02-22,Round 25,Atlético Madrid,,Espanyol,,,https://r2.thesportsdb.com/images/media/event/thumb/x9goh51751450232.jpg
2279637,2026-02-22,Round 25,Barcelona,,Levante,,,https://r2.thesportsdb.com/images/media/event/thumb/f7e0al1751450233.jpg
2279638,2026-02-22,Round 25,Real Betis,,Rayo Vallecano,,,https://r2.thesportsdb.com/images/media/event/thumb/r3gb8i1751450235.jpg
2279639,2026-02-22,Round 25,Celta Vigo,,Mallorca,,,https://r2.thesportsdb.com/images/media/event/thumb/vqs3ww1751450236.jpg
2279640,2026-02-22,Round 25,Getafe,,Sevilla,,,https://r2.thesportsdb.com/images/media/event/thumb/3lpu7v1751450238.jpg
2279641,2026-02-22,Round 25,Osasuna,,Real Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/f9x2qt1751450240.jpg
2279642,2026-02-22,Round 25,Real Sociedad,,Real Oviedo,,,https://r2.thesportsdb.com/images/media/event/thumb/zx928q1751450241.jpg
2279643,2026-02-22,Round 25,Villarreal,,Valencia,,,https://r2.thesportsdb.com/images/media/event/thumb/g8evsa1751450242.jpg
2279644,2026-03-01,Round 26,Barcelona,,Villarreal,,,https://r2.thesportsdb.com/images/media/event/thumb/pu7z9w1751450243.jpg
2279645,2026-03-01,Round 26,Real Betis,,Sevilla,,,https://r2.thesportsdb.com/images/media/event/thumb/2j1t3p1751450245.jpg
2279646,2026-03-01,Round 26,Elche,,Espanyol,,,https://r2.thesportsdb.com/images/media/event/thumb/g91lkw1751450246.jpg
2279647,2026-03-01,Round 26,Girona,,Celta Vigo,,,https://r2.thesportsdb.com/images/media/event/thumb/0zj3u61751450248.jpg
2279648,2026-03-01,Round 26,Levante,,Deportivo Alavés,,,https://r2.thesportsdb.com/images/media/event/thumb/womjiz1751450249.jpg
2279649,2026-03-01,Round 26,Mallorca,,Real Sociedad,,,https://r2.thesportsdb.com/images/media/event/thumb/yq5fjv1751450251.jpg
2279650,2026-03-01,Round 26,Rayo Vallecano,,Athletic Bilbao,,,https://r2.thesportsdb.com/images/media/event/thumb/imku851751450252.jpg
2279651,2026-03-01,Round 26,Real Madrid,,Getafe,,,https://r2.thesportsdb.com/images/media/event/thumb/39ir851751450254.jpg
2279652,2026-03-01,Round 26,Real Oviedo,,Atlético Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/jx5fyh1751450255.jpg
2279653,2026-03-01,Round 26,Valencia,,Osasuna,,,https://r2.thesportsdb.com/images/media/event/thumb/qgi1i01751450257.jpg
2279654,2026-03-08,Round 27,Athletic Bilbao,,Barcelona,,,https://r2.thesportsdb.com/images/media/event/thumb/izw7m21751450258.jpg
2279655,2026-03-08,Round 27,Atlético Madrid,,Real Sociedad,,,https://r2.thesportsdb.com/images/media/event/thumb/sd1tk31751450260.jpg
2279656,2026-03-08,Round 27,Celta Vigo,,Real Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/fqpne41751450262.jpg
2279657,2026-03-08,Round 27,Espanyol,,Real Oviedo,,,https://r2.thesportsdb.com/images/media/event/thumb/5bspqi1751450263.jpg
2279658,2026-03-08,Round 27,Getafe,,Real Betis,,,https://r2.thesportsdb.com/images/media/event/thumb/xqky5w1751450265.jpg
2279659,2026-03-08,Round 27,Levante,,Girona,,,https://r2.thesportsdb.com/images/media/event/thumb/byzp851751450266.jpg
2279660,2026-03-08,Round 27,Osasuna,,Mallorca,,,https://r2.thesportsdb.com/images/media/event/thumb/0z8khw1751450267.jpg
2279661,2026-03-08,Round 27,Sevilla,,Rayo Vallecano,,,https://r2.thesportsdb.com/images/media/event/thumb/v5kqwf1751450269.jpg
2279662,2026-03-08,Round 27,Valencia,,Deportivo Alavés,,,https://r2.thesportsdb.com/images/media/event/thumb/vcpfpk1751450270.jpg
2279663,2026-03-08,Round 27,Villarreal,,Elche,,,https://r2.thesportsdb.com/images/media/event/thumb/1pcijh1751450271.jpg
2279664,2026-03-15,Round 28,Deportivo Alavés,,Villarreal,,,https://r2.thesportsdb.com/images/media/event/thumb/o02hs51751450273.jpg
2279665,2026-03-15,Round 28,Atlético Madrid,,Getafe,,,https://r2.thesportsdb.com/images/media/event/thumb/auarqo1751450274.jpg
2279666,2026-03-15,Round 28,Barcelona,,Sevilla,,,https://r2.thesportsdb.com/images/media/event/thumb/z3rsti1751450276.jpg
2279667,2026-03-15,Round 28,Real Betis,,Celta Vigo,,,https://r2.thesportsdb.com/images/media/event/thumb/scxfe11751450277.jpg
2279668,2026-03-15,Round 28,Girona,,Athletic Bilbao,,,https://r2.thesportsdb.com/images/media/event/thumb/gb74a01751450279.jpg
2279669,2026-03-15,Round 28,Mallorca,,Espanyol,,,https://r2.thesportsdb.com/images/media/event/thumb/fquxfg1751450280.jpg
2279670,2026-03-15,Round 28,Rayo Vallecano,,Levante,,,https://r2.thesportsdb.com/images/media/event/thumb/sq7b3g1751450282.jpg
2279671,2026-03-15,Round 28,Real Madrid,,Elche,,,https://r2.thesportsdb.com/images/media/event/thumb/gsoov41751450283.jpg
2279672,2026-03-15,Round 28,Real Sociedad,,Osasuna,,,https://r2.thesportsdb.com/images/media/event/thumb/fxh6pg1751450285.jpg
2279673,2026-03-15,Round 28,Real Oviedo,,Valencia,,,https://r2.thesportsdb.com/images/media/event/thumb/sxh48i1751450287.jpg
2279674,2026-03-22,Round 29,Athletic Bilbao,,Real Betis,,,https://r2.thesportsdb.com/images/media/event/thumb/12vgnv1751450288.jpg
2279675,2026-03-22,Round 29,Barcelona,,Rayo Vallecano,,,https://r2.thesportsdb.com/images/media/event/thumb/nfy8x91751450289.jpg
2279676,2026-03-22,Round 29,Celta Vigo,,Deportivo Alavés,,,https://r2.thesportsdb.com/images/media/event/thumb/47wk4c1751450291.jpg
2279677,2026-03-22,Round 29,Elche,,Mallorca,,,https://r2.thesportsdb.com/images/media/event/thumb/815ikq1751450292.jpg
2279678,2026-03-22,Round 29,Espanyol,,Getafe,,,https://r2.thesportsdb.com/images/media/event/thumb/3z2tyx1751450294.jpg
2279679,2026-03-22,Round 29,Levante,,Real Oviedo,,,https://r2.thesportsdb.com/images/media/event/thumb/kn0jja1751450295.jpg
2279680,2026-03-22,Round 29,Osasuna,,Girona,,,https://r2.thesportsdb.com/images/media/event/thumb/cfpnmu1751450297.jpg
2279681,2026-03-22,Round 29,Real Madrid,,Atlético Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/uycl9d1751450298.jpg
2279682,2026-03-22,Round 29,Sevilla,,Valencia,,,https://r2.thesportsdb.com/images/media/event/thumb/0b6xhw1751450300.jpg
2279683,2026-03-22,Round 29,Villarreal,,Real Sociedad,,,https://r2.thesportsdb.com/images/media/event/thumb/14jbdq1751450301.jpg
2279684,2026-04-05,Round 30,Deportivo Alavés,,Osasuna,,,https://r2.thesportsdb.com/images/media/event/thumb/z82kvj1751450303.jpg
2279685,2026-04-05,Round 30,Atlético Madrid,,Barcelona,,,https://r2.thesportsdb.com/images/media/event/thumb/qv1b1d1751450304.jpg
2279686,2026-04-05,Round 30,Real Betis,,Espanyol,,,https://r2.thesportsdb.com/images/media/event/thumb/tgj1kk1751450305.jpg
2279687,2026-04-05,Round 30,Getafe,,Athletic Bilbao,,,https://r2.thesportsdb.com/images/media/event/thumb/299buj1751450307.jpg
2279688,2026-04-05,Round 30,Girona,,Villarreal,,,https://r2.thesportsdb.com/images/media/event/thumb/f0np4a1751450308.jpg
2279689,2026-04-05,Round 30,Mallorca,,Real Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/20f1ja1751450310.jpg
2279690,2026-04-05,Round 30,Rayo Vallecano,,Elche,,,https://r2.thesportsdb.com/images/media/event/thumb/ksug6u1751450311.jpg
2279691,2026-04-05,Round 30,Real Sociedad,,Levante,,,https://r2.thesportsdb.com/images/media/event/thumb/hfm6361751450313.jpg
2279692,2026-04-05,Round 30,Real Oviedo,,Sevilla,,,https://r2.thesportsdb.com/images/media/event/thumb/drnv2f1751450314.jpg
2279693,2026-04-05,Round 30,Valencia,,Celta Vigo,,,https://r2.thesportsdb.com/images/media/event/thumb/wom1zd1751450316.jpg
2279694,2026-04-12,Round 31,Athletic Bilbao,,Villarreal,,,https://r2.thesportsdb.com/images/media/event/thumb/62zfdr1751450317.jpg
2279695,2026-04-12,Round 31,Barcelona,,Espanyol,,,https://r2.thesportsdb.com/images/media/event/thumb/d8mpw51751450319.jpg
2279696,2026-04-12,Round 31,Celta Vigo,,Real Oviedo,,,https://r2.thesportsdb.com/images/media/event/thumb/vz8tqm1751450320.jpg
2279697,2026-04-12,Round 31,Elche,,Valencia,,,https://r2.thesportsdb.com/images/media/event/thumb/krczu61751450321.jpg
2279698,2026-04-12,Round 31,Levante,,Getafe,,,https://r2.thesportsdb.com/images/media/event/thumb/yikztj1751450322.jpg
2279699,2026-04-12,Round 31,Mallorca,,Rayo Vallecano,,,https://r2.thesportsdb.com/images/media/event/thumb/jg07581751450324.jpg
2279700,2026-04-12,Round 31,Osasuna,,Real Betis,,,https://r2.thesportsdb.com/images/media/event/thumb/agxlcc1751450326.jpg
2279701,2026-04-12,Round 31,Real Madrid,,Girona,,,https://r2.thesportsdb.com/images/media/event/thumb/5m2dy51751450327.jpg
2279702,2026-04-12,Round 31,Real Sociedad,,Deportivo Alavés,,,https://r2.thesportsdb.com/images/media/event/thumb/psdg0g1751450329.jpg
2279703,2026-04-12,Round 31,Sevilla,,Atlético Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/c34wmb1751450330.jpg
2279704,2026-04-19,Round 32,Deportivo Alavés,,Mallorca,,,https://r2.thesportsdb.com/images/media/event/thumb/pdul4v1751450332.jpg
2279705,2026-04-19,Round 32,Atlético Madrid,,Athletic Bilbao,,,https://r2.thesportsdb.com/images/media/event/thumb/go0c621751450333.jpg
2279706,2026-04-19,Round 32,Real Betis,,Real Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/n5uqqi1751450334.jpg
2279707,2026-04-19,Round 32,Espanyol,,Levante,,,https://r2.thesportsdb.com/images/media/event/thumb/jtgedz1751450336.jpg
2279708,2026-04-19,Round 32,Getafe,,Barcelona,,,https://r2.thesportsdb.com/images/media/event/thumb/7o7d3a1751450337.jpg
2279709,2026-04-19,Round 32,Osasuna,,Sevilla,,,https://r2.thesportsdb.com/images/media/event/thumb/edqmz11751450339.jpg
2279710,2026-04-19,Round 32,Rayo Vallecano,,Real Sociedad,,,https://r2.thesportsdb.com/images/media/event/thumb/me2dij1751450340.jpg
2279711,2026-04-19,Round 32,Real Oviedo,,Elche,,,https://r2.thesportsdb.com/images/media/event/thumb/4z9bir1751450342.jpg
2279712,2026-04-19,Round 32,Valencia,,Girona,,,https://r2.thesportsdb.com/images/media/event/thumb/rza2ti1751450343.jpg
2279713,2026-04-19,Round 32,Villarreal,,Celta Vigo,,,https://r2.thesportsdb.com/images/media/event/thumb/f71a4y1751450345.jpg
2279714,2026-04-22,Round 33,Athletic Bilbao,,Osasuna,,,https://r2.thesportsdb.com/images/media/event/thumb/bp9sts1751450346.jpg
2279715,2026-04-22,Round 33,Barcelona,,Celta Vigo,,,https://r2.thesportsdb.com/images/media/event/thumb/q2h4u21751450348.jpg
2279716,2026-04-22,Round 33,Elche,,Atlético Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/hs2yuz1751450349.jpg
2279717,2026-04-22,Round 33,Girona,,Real Betis,,,https://r2.thesportsdb.com/images/media/event/thumb/cm7ttn1751450350.jpg
2279718,2026-04-22,Round 33,Levante,,Sevilla,,,https://r2.thesportsdb.com/images/media/event/thumb/fygwvm1751450352.jpg
2279719,2026-04-22,Round 33,Mallorca,,Valencia,,,https://r2.thesportsdb.com/images/media/event/thumb/wg9z7f1751450354.jpg
2279720,2026-04-22,Round 33,Rayo Vallecano,,Espanyol,,,https://r2.thesportsdb.com/images/media/event/thumb/jui9hj1751450356.jpg
2279721,2026-04-22,Round 33,Real Madrid,,Deportivo Alavés,,,https://r2.thesportsdb.com/images/media/event/thumb/9crdzj1751450357.jpg
2279722,2026-04-22,Round 33,Real Sociedad,,Getafe,,,https://r2.thesportsdb.com/images/media/event/thumb/gez1tz1751450358.jpg
2279723,2026-04-22,Round 33,Real Oviedo,,Villarreal,,,https://r2.thesportsdb.com/images/media/event/thumb/zd9kk61751450360.jpg
2279724,2026-05-03,Round 34,Deportivo Alavés,,Athletic Bilbao,,,https://r2.thesportsdb.com/images/media/event/thumb/cvpjrf1751450361.jpg
2279725,2026-05-03,Round 34,Real Betis,,Real Oviedo,,,https://r2.thesportsdb.com/images/media/event/thumb/yanc971751450363.jpg
2279726,2026-05-03,Round 34,Celta Vigo,,Elche,,,https://r2.thesportsdb.com/images/media/event/thumb/9ovzxz1751450364.jpg
2279727,2026-05-03,Round 34,Espanyol,,Real Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/fvi2qe1751450366.jpg
2279728,2026-05-03,Round 34,Getafe,,Rayo Vallecano,,,https://r2.thesportsdb.com/images/media/event/thumb/1u8cl71751450367.jpg
2279729,2026-05-03,Round 34,Girona,,Mallorca,,,https://r2.thesportsdb.com/images/media/event/thumb/qn8nlr1751450368.jpg
2279730,2026-05-03,Round 34,Osasuna,,Barcelona,,,https://r2.thesportsdb.com/images/media/event/thumb/r686pw1751450370.jpg
2279731,2026-05-03,Round 34,Sevilla,,Real Sociedad,,,https://r2.thesportsdb.com/images/media/event/thumb/jr1yz41751450372.jpg
2279732,2026-05-03,Round 34,Valencia,,Atlético Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/td71mh1751450373.jpg
2279733,2026-05-03,Round 34,Villarreal,,Levante,,,https://r2.thesportsdb.com/images/media/event/thumb/6dohev1751450375.jpg
2279734,2026-05-10,Round 35,Athletic Bilbao,,Valencia,,,https://r2.thesportsdb.com/images/media/event/thumb/pptim81751450376.jpg
2279735,2026-05-10,Round 35,Atlético Madrid,,Celta Vigo,,,https://r2.thesportsdb.com/images/media/event/thumb/c1hyzd1751450378.jpg
2279736,2026-05-10,Round 35,Barcelona,,Real Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/hgt4bz1751450379.jpg
2279737,2026-05-10,Round 35,Elche,,Deportivo Alavés,,,https://r2.thesportsdb.com/images/media/event/thumb/55otif1751450380.jpg
2279738,2026-05-10,Round 35,Levante,,Osasuna,,,https://r2.thesportsdb.com/images/media/event/thumb/r2hwkq1751450382.jpg
2279739,2026-05-10,Round 35,Mallorca,,Villarreal,,,https://r2.thesportsdb.com/images/media/event/thumb/b2ofn91751450383.jpg
2279740,2026-05-10,Round 35,Rayo Vallecano,,Girona,,,https://r2.thesportsdb.com/images/media/event/thumb/rlgaln1751450384.jpg
2279741,2026-05-10,Round 35,Real Sociedad,,Real Betis,,,https://r2.thesportsdb.com/images/media/event/thumb/zby5mh1751450386.jpg
2279742,2026-05-10,Round 35,Real Oviedo,,Getafe,,,https://r2.thesportsdb.com/images/media/event/thumb/pcuwu11751450387.jpg
2279743,2026-05-10,Round 35,Sevilla,,Espanyol,,,https://r2.thesportsdb.com/images/media/event/thumb/5ctly41751450389.jpg
2279744,2026-05-13,Round 36,Deportivo Alavés,,Barcelona,,,https://r2.thesportsdb.com/images/media/event/thumb/ahxf4t1751450390.jpg
2279745,2026-05-13,Round 36,Real Betis,,Elche,,,https://r2.thesportsdb.com/images/media/event/thumb/uui0y71751450392.jpg
2279746,2026-05-13,Round 36,Celta Vigo,,Levante,,,https://r2.thesportsdb.com/images/media/event/thumb/5osquc1751450393.jpg
2279747,2026-05-13,Round 36,Espanyol,,Athletic Bilbao,,,https://r2.thesportsdb.com/images/media/event/thumb/6248yn1751450395.jpg
2279748,2026-05-13,Round 36,Getafe,,Mallorca,,,https://r2.thesportsdb.com/images/media/event/thumb/2xflhc1751450396.jpg
2279749,2026-05-13,Round 36,Girona,,Real Sociedad,,,https://r2.thesportsdb.com/images/media/event/thumb/5yo5p01751450397.jpg
2279750,2026-05-13,Round 36,Osasuna,,Atlético Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/ndr9681751450399.jpg
2279751,2026-05-13,Round 36,Real Madrid,,Real Oviedo,,,https://r2.thesportsdb.com/images/media/event/thumb/2frfx91751450401.jpg
2279752,2026-05-13,Round 36,Valencia,,Rayo Vallecano,,,https://r2.thesportsdb.com/images/media/event/thumb/maedmq1751450402.jpg
2279753,2026-05-13,Round 36,Villarreal,,Sevilla,,,https://r2.thesportsdb.com/images/media/event/thumb/4h846b1751450403.jpg
2279754,2026-05-17,Round 37,Athletic Bilbao,,Celta Vigo,,,https://r2.thesportsdb.com/images/media/event/thumb/6r4vnl1751450405.jpg
2279755,2026-05-17,Round 37,Atlético Madrid,,Girona,,,https://r2.thesportsdb.com/images/media/event/thumb/uo528q1751450406.jpg
2279756,2026-05-17,Round 37,Barcelona,,Real Betis,,,https://r2.thesportsdb.com/images/media/event/thumb/vvhgkv1751450408.jpg
2279757,2026-05-17,Round 37,Elche,,Getafe,,,https://r2.thesportsdb.com/images/media/event/thumb/d8m2ts1751450409.jpg
2279758,2026-05-17,Round 37,Levante,,Mallorca,,,https://r2.thesportsdb.com/images/media/event/thumb/if890l1751450411.jpg
2279759,2026-05-17,Round 37,Osasuna,,Espanyol,,,https://r2.thesportsdb.com/images/media/event/thumb/3u2eja1751450412.jpg
2279760,2026-05-17,Round 37,Rayo Vallecano,,Villarreal,,,https://r2.thesportsdb.com/images/media/event/thumb/yngko51751450413.jpg
2279761,2026-05-17,Round 37,Real Sociedad,,Valencia,,,https://r2.thesportsdb.com/images/media/event/thumb/wijsdl1751450415.jpg
2279762,2026-05-17,Round 37,Real Oviedo,,Deportivo Alavés,,,https://r2.thesportsdb.com/images/media/event/thumb/1lgips1751450417.jpg
2279763,2026-05-17,Round 37,Sevilla,,Real Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/ve9fps1751450418.jpg
2279764,2026-05-24,Round 38,Deportivo Alavés,,Rayo Vallecano,,,https://r2.thesportsdb.com/images/media/event/thumb/1b0phc1751450419.jpg
2279765,2026-05-24,Round 38,Real Betis,,Levante,,,https://r2.thesportsdb.com/images/media/event/thumb/wpao291751450421.jpg
2279766,2026-05-24,Round 38,Celta Vigo,,Sevilla,,,https://r2.thesportsdb.com/images/media/event/thumb/n6q8fl1751450422.jpg
2279767,2026-05-24,Round 38,Espanyol,,Real Sociedad,,,https://r2.thesportsdb.com/images/media/event/thumb/yqubm71751450424.jpg
2279768,2026-05-24,Round 38,Getafe,,Osasuna,,,https://r2.thesportsdb.com/images/media/event/thumb/z0rdm41751450425.jpg
2279769,2026-05-24,Round 38,Girona,,Elche,,,https://r2.thesportsdb.com/images/media/event/thumb/sdzfmv1751450426.jpg
2279770,2026-05-24,Round 38,Mallorca,,Real Oviedo,,,https://r2.thesportsdb.com/images/media/event/thumb/gkh9kz1751450428.jpg
2279771,2026-05-24,Round 38,Real Madrid,,Athletic Bilbao,,,https://r2.thesportsdb.com/images/media/event/thumb/6c9pg71751450429.jpg
2279772,2026-05-24,Round 38,Valencia,,Barcelona,,,https://r2.thesportsdb.com/images/media/event/thumb/avveni1751450431.jpg
2279773,2026-05-24,Round 38,Villarreal,,Atlético Madrid,,,https://r2.thesportsdb.com/images/media/event/thumb/na2zs81751450432.jpg
"""

# Here you would add ALL the remaining rounds from your original data...
# For now, I'll help you check the current entries and then you can add the complete data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("=== LaLiga COMPLETE Matchday Initialization ===")
    
    try:
        # Parse the CSV to see how many we have
        lines = [line for line in LALIGA_2024_25_COMPLETE_FIXTURES.split('\n') if line.strip()]
        logger.info(f"CSV contains {len(lines)} fixtures")
        
        # Count unique rounds
        rounds = set()
        for line in lines:
            parts = line.split(',')
            if len(parts) >= 3:
                round_str = parts[2].replace('Round ', '')
                try:
                    rounds.add(int(round_str))
                except ValueError:
                    pass
        
        logger.info(f"CSV contains {len(rounds)} unique matchdays: {sorted(rounds)}")
        
        results = initialize_laliga_matchdays(LALIGA_2024_25_COMPLETE_FIXTURES)
        
        print("\n" + "="*80)
        print("INITIALIZATION COMPLETE!")
        print("="*80)
        print(f"Matchdays created/updated: {results.get('matchdays_created', 0)}")
        print(f"Matches linked: {results.get('matches_updated', 0)}")
        
        if results.get('errors'):
            print(f"Errors: {len(results['errors'])}")
            for error in results['errors'][:3]:
                print(f"   - {error}")
        
        print(f"\nProcessed {len(lines)} fixtures")
        print(f"Found {len(rounds)} unique matchdays")
        
        print("\nFeatures now active:")
        print("Real LaLiga schedule integration")
        print("Transfer locks during active matchdays")
        print("Automatic points calculation when matchdays finish")
        
        print("\nNext steps:")
        print("Run: python check_matchdays.py")
        print("Test API: curl http://localhost:5000/matchdays/current")
        
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        sys.exit(1)
