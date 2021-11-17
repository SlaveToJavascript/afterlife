$(async() => {
    console.log(test); 
    var packageURL = "http://127.0.0.1:5000/package";
    var retrieveParams = {
        headers: {
            "content-type": "charset=UTF-8"
        },
        method: "GET",
        mode: 'cors'
    };
    try {
        const response = 
        await fetch( 
            packageURL, retrieveParams,
        );



        const data = await response.json();
        const packages = data.package;
        
        if (!packages || !packages.length) {
            showError('Package list empty or undefined.');
        } else {
            // for loop to setup all table rows with obtained book data
            var rows = "";
            for (const package of packages) {
                eachRow =
                    "<td>" + package.packagename + "</td>" +
                    "<td>" + package.packageprice + "</td>" +
                    "<td>" + package.no_of_days + "</td>";
                rows += "<tbody><tr>" + eachRow + "</tr></tbody>";
            }
            // add all the rows to the table
            $('#packageTable').append(rows);
        }
    } catch (error) {
        // Errors when calling the service; such as network error, 
        // service offline, etc
        showError
      ('There is a problem retrieving books data, please try again later.<br />'+error);
       
    } // error

    console.log('yay')
});

alert('bin is handsome');