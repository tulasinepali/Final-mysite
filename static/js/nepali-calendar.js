/**
 * Nepali Bikram Sambat (B.S.) <-> Gregorian (A.D.) Calendar Library
 * High-precision astronomical calendar data verified from 1978 B.S. to 2099 B.S.
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

    // Number of days in each BS month from 1978 to 2099 BS
    // Array order: [Baisakh, Jestha, Ashadh, Shrawan, Bhadra, Ashwin, Kartik, Mangsir, Poush, Magh, Falgun, Chaitra]
    var bsCalendarData = {
        1978: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        1979: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        1980: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        1981: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
        1982: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        1983: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        1984: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        1985: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
        1986: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        1987: [31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        1988: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        1989: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        1990: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        1991: [31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        1992: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        1993: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        1994: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        1995: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        1996: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        1997: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        1998: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        1999: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2000: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2001: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2002: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2003: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2004: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2005: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2006: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2007: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2008: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 29, 31],
        2009: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2010: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2011: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2012: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
        2013: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2014: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2015: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2016: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
        2017: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2018: [31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2019: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2020: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2021: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2022: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        2023: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2024: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2025: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2026: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2027: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2028: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2029: [31, 31, 32, 31, 32, 30, 30, 29, 30, 29, 30, 30],
        2030: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2031: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2032: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2033: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2034: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2035: [30, 32, 31, 32, 31, 31, 29, 30, 30, 29, 29, 31],
        2036: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2037: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2038: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2039: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
        2040: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2041: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2042: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2043: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
        2044: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2045: [31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2046: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2047: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2048: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2049: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        2050: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2051: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2052: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2053: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        2054: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2055: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2056: [31, 31, 32, 31, 32, 30, 30, 29, 30, 29, 30, 30],
        2057: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2058: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2059: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2060: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2061: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2062: [30, 32, 31, 32, 31, 31, 29, 30, 29, 30, 29, 31],
        2063: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2064: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2065: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2066: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 29, 31],
        2067: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2068: [31, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2069: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2070: [31, 31, 31, 32, 31, 31, 29, 30, 30, 29, 30, 30],
        2071: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2072: [31, 32, 31, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2073: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
        2074: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2075: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2076: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        2077: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2078: [31, 31, 31, 32, 31, 31, 30, 29, 30, 29, 30, 30],
        2079: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2080: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 30],
        2081: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 29, 31],
        2082: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2083: [31, 31, 32, 31, 31, 31, 30, 29, 30, 29, 30, 30],
        2084: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2085: [31, 32, 31, 32, 30, 31, 30, 30, 29, 30, 30, 30],
        2086: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2087: [31, 31, 32, 31, 31, 31, 30, 30, 29, 30, 30, 30],
        2088: [30, 31, 32, 32, 30, 31, 30, 30, 29, 30, 30, 30],
        2089: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2090: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2091: [31, 31, 32, 31, 31, 31, 30, 30, 29, 30, 30, 30],
        2092: [30, 31, 32, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2093: [30, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2094: [31, 31, 32, 31, 31, 30, 30, 30, 29, 30, 30, 30],
        2095: [31, 31, 32, 31, 31, 31, 30, 29, 30, 30, 30, 30],
        2096: [30, 31, 32, 32, 31, 30, 30, 29, 30, 29, 30, 30],
        2097: [31, 32, 31, 32, 31, 30, 30, 30, 29, 30, 30, 30],
        2098: [31, 31, 32, 31, 31, 31, 29, 30, 29, 30, 29, 31],
        2099: [31, 32, 31, 32, 31, 30, 30, 30, 29, 29, 30, 31],
    };

    var MIN_YEAR_BS = 1978;
    var MAX_YEAR_BS = 2099;
    var START_ENGLISH_DATE = '1921-04-13'; // Corresponds to 1978-01-01 B.S.

    var BS_MONTHS_EN = ["Baishakh", "Jestha", "Ashadh", "Shrawan", "Bhadra", "Ashwin", "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra"];
    var BS_MONTHS_NE = ["वैशाख", "जेठ", "असार", "साउन", "भदौ", "असोज", "कार्तिक", "मंसिर", "पुस", "माघ", "फागुन", "चैत"];
    var DAYS_EN = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    var DAYS_NE = ["आइतबार", "सोमबार", "मंगलबार", "बुधबार", "बिहीबार", "शुक्रबार", "शनिबार"];
    var NE_DIGITS = ['०', '१', '२', '३', '४', '५', '६', '७', '८', '९'];

    function toNepaliDigits(num) {
        return String(num).replace(/[0-9]/g, function (d) {
            return NE_DIGITS[parseInt(d, 10)];
        });
    }

    function padZero(num) {
        return num < 10 ? '0' + num : String(num);
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
        bsYear = parseInt(bsYear, 10);
        bsMonth = parseInt(bsMonth, 10);
        bsDay = parseInt(bsDay, 10);

        if (bsYear < MIN_YEAR_BS || bsYear > MAX_YEAR_BS || !bsCalendarData[bsYear]) {
            throw new Error("Year outside supported range (" + MIN_YEAR_BS + " - " + MAX_YEAR_BS + " B.S.)");
        }
        if (bsMonth < 1 || bsMonth > 12) {
            throw new Error("Invalid B.S. Month (1 - 12)");
        }
        var maxDays = bsCalendarData[bsYear][bsMonth - 1];
        if (bsDay < 1 || bsDay > maxDays) {
            throw new Error("Invalid Day for " + BS_MONTHS_EN[bsMonth - 1] + " " + bsYear + " (Max " + maxDays + " days)");
        }

        var daysDiff = 0;
        for (var y = MIN_YEAR_BS; y <= bsYear; y++) {
            if (y === bsYear) {
                for (var m = 1; m < bsMonth; m++) {
                    daysDiff += bsCalendarData[y][m - 1];
                }
                daysDiff += (bsDay - 1);
            } else {
                for (var mAll = 1; mAll <= 12; mAll++) {
                    daysDiff += bsCalendarData[y][mAll - 1];
                }
            }
        }

        // Calculate Gregorian date starting from 1921-04-13 (UTC)
        var startAd = new Date(Date.UTC(1921, 3, 13));
        startAd.setUTCDate(startAd.getUTCDate() + daysDiff);

        var adYear = startAd.getUTCFullYear();
        var adMonth = startAd.getUTCMonth() + 1;
        var adDay = startAd.getUTCDate();
        var dayOfWeek = startAd.getUTCDay();

        return {
            adYear: adYear,
            adMonth: adMonth,
            adDay: adDay,
            dayOfWeek: dayOfWeek,
            dayNameEn: DAYS_EN[dayOfWeek],
            dayNameNe: DAYS_NE[dayOfWeek],
            formattedAd: adYear + "-" + padZero(adMonth) + "-" + padZero(adDay),
            formattedBsNe: toNepaliDigits(bsYear) + " " + BS_MONTHS_NE[bsMonth - 1] + " " + toNepaliDigits(bsDay) + " गते, " + DAYS_NE[dayOfWeek]
        };
    }

    // Convert A.D. Date to B.S. Date
    function adToBs(adYear, adMonth, adDay) {
        adYear = parseInt(adYear, 10);
        adMonth = parseInt(adMonth, 10);
        adDay = parseInt(adDay, 10);

        var startAd = new Date(Date.UTC(1921, 3, 13));
        var targetAd = new Date(Date.UTC(adYear, adMonth - 1, adDay));
        var daysDiff = Math.floor((targetAd.getTime() - startAd.getTime()) / 86400000);

        if (daysDiff < 0) {
            throw new Error("Date outside supported range (Min: April 13, 1921 A.D.)");
        }

        var bsYear = 0;
        var bsMonth = 0;
        var bsDay = 0;
        var totalD = 0;
        var found = false;

        for (var y = MIN_YEAR_BS; y <= MAX_YEAR_BS; y++) {
            if (found) break;
            for (var m = 1; m <= 12; m++) {
                totalD += bsCalendarData[y][m - 1];
                if (daysDiff - totalD < 0) {
                    bsDay = daysDiff - totalD + bsCalendarData[y][m - 1] + 1;
                    bsYear = y;
                    bsMonth = m;
                    found = true;
                    break;
                }
            }
        }

        if (!found) {
            throw new Error("Date outside supported range (Max: 2099 B.S.)");
        }

        var dayOfWeek = targetAd.getUTCDay();

        return {
            bsYear: bsYear,
            bsMonth: bsMonth,
            bsDay: bsDay,
            dayOfWeek: dayOfWeek,
            monthNameEn: BS_MONTHS_EN[bsMonth - 1],
            monthNameNe: BS_MONTHS_NE[bsMonth - 1],
            dayNameEn: DAYS_EN[dayOfWeek],
            dayNameNe: DAYS_NE[dayOfWeek],
            formattedBs: bsYear + "-" + padZero(bsMonth) + "-" + padZero(bsDay),
            formattedBsNe: toNepaliDigits(bsYear) + " " + BS_MONTHS_NE[bsMonth - 1] + " " + toNepaliDigits(bsDay) + " गते, " + DAYS_NE[dayOfWeek]
        };
    }

    // Get today's B.S. Date based on client / local time
    function getTodayBs() {
        var now = new Date();
        return adToBs(now.getFullYear(), now.getMonth() + 1, now.getDate());
    }

    // Universal Age Calculator
    function calculateAge(dobYear, dobMonth, dobDay, isDobBs, targetYear, targetMonth, targetDay, isTargetBs) {
        var dobAd = isDobBs ? bsToAd(dobYear, dobMonth, dobDay) : { adYear: parseInt(dobYear, 10), adMonth: parseInt(dobMonth, 10), adDay: parseInt(dobDay, 10) };
        var targetAd = isTargetBs ? bsToAd(targetYear, targetMonth, targetDay) : { adYear: parseInt(targetYear, 10), adMonth: parseInt(targetMonth, 10), adDay: parseInt(targetDay, 10) };

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
        var totalDays = Math.floor(diffTime / 86400000);
        var totalWeeks = Math.floor(totalDays / 7);
        var totalMonths = (y * 12) + m;

        // Next birthday calculation
        var nextBday = new Date(Date.UTC(targetAd.adYear, dobAd.adMonth - 1, dobAd.adDay));
        if (nextBday < target) {
            nextBday.setUTCFullYear(targetAd.adYear + 1);
        }
        var daysToNextBday = Math.ceil((nextBday.getTime() - target.getTime()) / 86400000);

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
        bsCalendarData: bsCalendarData,
        MIN_YEAR_BS: MIN_YEAR_BS,
        MAX_YEAR_BS: MAX_YEAR_BS
    };
}));
