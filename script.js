function doGet(e) {
    const sheet = SpreadsheetApp
        .getActiveSpreadsheet()
        .getSheetByName("Sheet1"); // change if needed

    const data = sheet.getDataRange().getValues();
    const headers = data.shift();

    const jsonData = data.map(row => {
        let obj = {};
        headers.forEach((h, i) => obj[h] = row[i]);
        return obj;
    });

    return ContentService
        .createTextOutput(JSON.stringify(jsonData))
        .setMimeType(ContentService.MimeType.JSON);
}
