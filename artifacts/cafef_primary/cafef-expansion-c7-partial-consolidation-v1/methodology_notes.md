# C7 acquisition inventory

Inventory phân biệt acquisition completeness với market-session completeness. `NOT_YET_ACQUIRED`/`ACQUISITION_PARTIAL` không phải `MISSING_ON_TRADEHISTORYNEW`, suspension, not-listed hoặc confirmed provider gap. Empty provider page chỉ là neutral provider/history boundary. Supplemental crawl giữ null khác zero, không fabricate row, không timeline compression và không overwrite năm ZIP ban đầu.
