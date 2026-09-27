/**
 * Nepali Bikram Sambat (B.S.) <-> Gregorian (A.D.) Calendar Library
 * Accurate for years 1970 B.S. to 2100 B.S.
 * Built for tulasinepali.com.np
 */

(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        define([], factory);
    } else if (typeof module === 'object' && module.exports) {
        module.exports = factory();
    } else {
        root.NepaliCalendar = factory();
    }
}(typeof self !== 'undefined' ? self : this, function () {

    // Number of days in each BS month from 1970 to 2100 BS
    // Array order: [Baisakh, Jestha, Ashadh, Shrawan, Bhadra, Ashwin, Kartik, Mangsir, Poush, Magh, Falgun, Chaitra]
    var bsCalendarData = {
        1970: [31, 31, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        1971: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 29, 31],
        1972: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        1973: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        1974: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        1975: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        1976: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        1977: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        1978: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        1979: [31, 31, 32, 31, 31, 31, 29, 30, 29, 30, 29, 31],
        1980: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        1981: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        1982: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        1983: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        1984: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        1985: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        1986: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        1987: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        1988: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        1989: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        1990: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        1991: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        1992: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        1993: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        1994: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        1995: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        1996: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        1997: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        1998: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        1999: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2000: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2001: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2002: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2003: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2004: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2005: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2006: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2007: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2008: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2009: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2010: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2011: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2012: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2013: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2014: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2015: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2016: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2017: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2018: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2019: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2020: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2021: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2022: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2023: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2024: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2025: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2026: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2027: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2028: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2029: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2030: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2031: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2032: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2033: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2034: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2035: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2036: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2037: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2038: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2039: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2040: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2041: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2042: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2043: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2044: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2045: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2046: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2047: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2048: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2049: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2050: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2051: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2052: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2053: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2054: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2055: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2056: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2057: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2058: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2059: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2060: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2061: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2062: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2063: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2064: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2065: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2066: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2067: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2068: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2069: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2070: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2071: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2072: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2073: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2074: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2075: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2076: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2077: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2078: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2079: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2080: [31, 32, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2081: [31, 31, 32, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2082: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2083: [31, 31, 32, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2084: [31, 31, 32, 31, 32, 30, 30, 30, 29, 30, 30, 30],
        2085: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2086: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2087: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2088: [31, 31, 32, 31, 32, 30, 30, 30, 29, 30, 30, 30],
        2089: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2090: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2091: [31, 31, 32, 31, 32, 30, 30, 30, 29, 30, 30, 30],
        2092: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2093: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2094: [31, 31, 32, 31, 32, 30, 30, 30, 29, 30, 30, 30],
        2095: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2096: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2097: [31, 31, 32, 31, 32, 30, 30, 30, 29, 30, 30, 30],
        2098: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2099: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2100: [31, 31, 32, 31, 32, 30, 30, 30, 29, 30, 30, 30]
    };

    // Reference dates: 2000-01-01 B.S. corresponds to 1943-04-14 A.D. (Wednesday)
    var REF_BS_YEAR = 2000;
    var REF_AD_YEAR = 1943;
    var REF_AD_MONTH = 4; // April
    var REF_AD_DAY = 14;

    var BS_MONTHS_EN = ["Baishakh", "Jestha", "Ashadh", "Shrawan", "Bhadra", "Ashwin", "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra"];
    var BS_MONTHS_NE = ["वैशाख", "जेठ", "असार", "साउन", "भदौ", "असोज", "कार्तिक", "मंसिर", "पुस", "माघ", "फागुन", "चैत"];
    var DAYS_EN = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    var DAYS_NE = ["आइतबार", "सोमबार", "मंगलबार", "बुधबार", "बिहीबार", "शुक्रबार", "शनिबार"];
    var NE_DIGITS = ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९'];

    function toNepaliDigits(num) {
        return String(num).replace(/[0-9]/g, function (d) {
            return NE_DIGITS[parseInt(d)];
        });
    }

    function isLeapYearAd(year) {
        return (year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0);
    }

    var AD_MONTH_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

    function getAdDaysInMonth(year, month) {
        if (month === 2 && isLeapYearAd(year)) return 29;
        return AD_MONTH_DAYS[month - 1];
    }

    // Convert B.S. Date to A.D. Date
    function bsToAd(bsYear, bsMonth, bsDay) {
        bsYear = parseInt(bsYear);
        bsMonth = parseInt(bsMonth);
        bsDay = parseInt(bsDay);

        if (!bsCalendarData[bsYear]) {
            throw new Error("Year outside supported range (1970 - 2100 B.S.)");
        }
        if (bsMonth < 1 || bsMonth > 12) {
            throw new Error("Invalid B.S. Month (1 - 12)");
        }
        var maxDays = bsCalendarData[bsYear][bsMonth - 1];
        if (bsDay < 1 || bsDay > maxDays) {
            throw new Error("Invalid Day for " + BS_MONTHS_EN[bsMonth - 1] + " " + bsYear + " (Max " + maxDays + " days)");
        }

        // Count total days from REF_BS (2000-01-01)
        var totalDays = 0;
        var y;
        if (bsYear >= REF_BS_YEAR) {
            for (y = REF_BS_YEAR; y < bsYear; y++) {
                var months = bsCalendarData[y];
                for (var m = 0; m < 12; m++) totalDays += months[m];
            }
            for (var m1 = 0; m1 < bsMonth - 1; m1++) {
                totalDays += bsCalendarData[bsYear][m1];
            }
            totalDays += (bsDay - 1);
        } else {
            for (y = bsYear; y < REF_BS_YEAR; y++) {
                var monthsOld = bsCalendarData[y];
                for (var mo = 0; mo < 12; mo++) totalDays -= monthsOld[mo];
            }
            for (var m2 = 0; m2 < bsMonth - 1; m2++) {
                totalDays += bsCalendarData[bsYear][m2];
            }
            totalDays += (bsDay - 1);
        }

        // Add totalDays to REF_AD (1943-04-14)
        var refDate = new Date(Date.UTC(REF_AD_YEAR, REF_AD_MONTH - 1, REF_AD_DAY));
        refDate.setUTCDate(refDate.getUTCDate() + totalDays);

        var adYear = refDate.getUTCFullYear();
        var adMonth = refDate.getUTCMonth() + 1;
        var adDay = refDate.getUTCDate();
        var dayOfWeek = refDate.getUTCDay();

        return {
            adYear: adYear,
            adMonth: adMonth,
            adDay: adDay,
            dayOfWeek: dayOfWeek,
            dayNameEn: DAYS_EN[dayOfWeek],
            dayNameNe: DAYS_NE[dayOfWeek],
            formattedAd: adYear + "-" + (adMonth < 10 ? "0" + adMonth : adMonth) + "-" + (adDay < 10 ? "0" + adDay : adDay),
            formattedBsNe: toNepaliDigits(bsYear) + " " + BS_MONTHS_NE[bsMonth - 1] + " " + toNepaliDigits(bsDay) + " गते, " + DAYS_NE[dayOfWeek]
        };
    }

    // Convert A.D. Date to B.S. Date
    function adToBs(adYear, adMonth, adDay) {
        adYear = parseInt(adYear);
        adMonth = parseInt(adMonth);
        adDay = parseInt(adDay);

        var targetDate = new Date(Date.UTC(adYear, adMonth - 1, adDay));
        var refDate = new Date(Date.UTC(REF_AD_YEAR, REF_AD_MONTH - 1, REF_AD_DAY));
        var diffTime = targetDate.getTime() - refDate.getTime();
        var totalDays = Math.round(diffTime / (1000 * 60 * 60 * 24));

        var bsYear = REF_BS_YEAR;
        var bsMonth = 1;
        var bsDay = 1;

        if (totalDays >= 0) {
            while (totalDays > 0) {
                var daysInCurMonth = bsCalendarData[bsYear][bsMonth - 1];
                if (totalDays >= daysInCurMonth) {
                    totalDays -= daysInCurMonth;
                    bsMonth++;
                    if (bsMonth > 12) {
                        bsMonth = 1;
                        bsYear++;
                        if (!bsCalendarData[bsYear]) {
                            throw new Error("Date outside supported range (max 2100 B.S.)");
                        }
                    }
                } else {
                    bsDay += totalDays;
                    totalDays = 0;
                }
            }
        } else {
            while (totalDays < 0) {
                bsMonth--;
                if (bsMonth < 1) {
                    bsMonth = 12;
                    bsYear--;
                    if (!bsCalendarData[bsYear]) {
                        throw new Error("Date outside supported range (min 1970 B.S.)");
                    }
                }
                var daysInPrevMonth = bsCalendarData[bsYear][bsMonth - 1];
                totalDays += daysInPrevMonth;
            }
            bsDay += totalDays;
        }

        var dayOfWeek = targetDate.getUTCDay();

        return {
            bsYear: bsYear,
            bsMonth: bsMonth,
            bsDay: bsDay,
            dayOfWeek: dayOfWeek,
            monthNameEn: BS_MONTHS_EN[bsMonth - 1],
            monthNameNe: BS_MONTHS_NE[bsMonth - 1],
            dayNameEn: DAYS_EN[dayOfWeek],
            dayNameNe: DAYS_NE[dayOfWeek],
            formattedBs: bsYear + "-" + (bsMonth < 10 ? "0" + bsMonth : bsMonth) + "-" + (bsDay < 10 ? "0" + bsDay : bsDay),
            formattedBsNe: toNepaliDigits(bsYear) + " " + BS_MONTHS_NE[bsMonth - 1] + " " + toNepaliDigits(bsDay) + " गते, " + DAYS_NE[dayOfWeek]
        };
    }

    // Get today's B.S. Date
    function getTodayBs() {
        var now = new Date();
        return adToBs(now.getFullYear(), now.getMonth() + 1, now.getDate());
    }

    // Universal Age Calculator
    function calculateAge(dobYear, dobMonth, dobDay, isDobBs, targetYear, targetMonth, targetDay, isTargetBs) {
        var dobAd = isDobBs ? bsToAd(dobYear, dobMonth, dobDay) : { adYear: parseInt(dobYear), adMonth: parseInt(dobMonth), adDay: parseInt(dobDay) };
        var targetAd = isTargetBs ? bsToAd(targetYear, targetMonth, targetDay) : { adYear: parseInt(targetYear), adMonth: parseInt(targetMonth), adDay: parseInt(targetDay) };

        var birth = new Date(Date.UTC(dobAd.adYear, dobAd.adMonth - 1, dobAd.adDay));
        var target = new Date(Date.UTC(targetAd.adYear, targetAd.adMonth - 1, targetAd.adDay));

        if (birth > target) {
            throw new Error("Date of Birth cannot be later than the target calculation date.");
        }

        var y = targetAd.adYear - dobAd.adYear;
        var m = targetAd.adMonth - dobAd.adMonth;
        var d = targetAd.adDay - dobAd.adDay;

        if (d < 0) {
            m--;
            var prevMonthDays = getAdDaysInMonth(targetAd.adYear, targetAd.adMonth === 1 ? 12 : targetAd.adMonth - 1);
            d += prevMonthDays;
        }
        if (m < 0) {
            y--;
            m += 12;
        }

        var diffTime = target.getTime() - birth.getTime();
        var totalDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
        var totalWeeks = Math.floor(totalDays / 7);
        var totalMonths = (y * 12) + m;

        // Next birthday calculation
        var nextBday = new Date(Date.UTC(targetAd.adYear, dobAd.adMonth - 1, dobAd.adDay));
        if (nextBday < target) {
            nextBday.setUTCFullYear(targetAd.adYear + 1);
        }
        var daysToNextBday = Math.ceil((nextBday.getTime() - target.getTime()) / (1000 * 60 * 60 * 24));

        return {
            years: y,
            months: m,
            days: d,
            totalDays: totalDays,
            totalWeeks: totalWeeks,
            totalMonths: totalMonths,
            daysToNextBirthday: daysToNextBday,
            summaryEn: y + " Years, " + m + " Months, " + d + " Days",
            summaryNe: toNepaliDigits(y) + " वर्ष, " + toNepaliDigits(m) + " महिना, " + toNepaliDigits(d) + " दिन"
        };
    }

    return {
        bsToAd: bsToAd,
        adToBs: adToBs,
        getTodayBs: getTodayBs,
        calculateAge: calculateAge,
        toNepaliDigits: toNepaliDigits,
        BS_MONTHS_EN: BS_MONTHS_EN,
        BS_MONTHS_NE: BS_MONTHS_NE,
        DAYS_EN: DAYS_EN,
        DAYS_NE: DAYS_NE,
        bsCalendarData: bsCalendarData
    };
}));
