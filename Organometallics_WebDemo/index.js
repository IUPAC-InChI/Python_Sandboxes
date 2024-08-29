const pyodidePromise = startPyodide();

async function startPyodide() {
    const pyodide = await loadPyodide();

    await pyodide.loadPackage("micropip");
    const micropip = pyodide.pyimport("micropip");
    await micropip.install(["antlr4-python3-runtime==4.11.1", "plotly"]);

    const packages = [ 
        "pandas",       
        "scipy",
        "networkx",
        "dist/tucan-0.1.0-py2.py3-none-any.whl"
    ];
    await pyodide.loadPackage(packages);
    
    await downloadFile("yapyinchi.py", pyodide);
    await downloadFile("metallic_elements.py", pyodide);
    await downloadFile("disconnection_table.py", pyodide);
    await downloadFile("libinchi.so", pyodide);

    await downloadFile("main.py", pyodide);
    // await loadPyModule("main.py", pyodide);

    console.log("pyodide is ready!")
    return pyodide;
}

async function downloadFile(name, pyodide) {
    await pyodide.runPythonAsync(`
        from pyodide.http import pyfetch
        response = await pyfetch("${name}", cache="no-store")
        with open("${name}", "wb") as f:
            f.write(await response.bytes())
    `)
}

async function clearForm() {
    document.getElementById("statusText").innerHTML = "";
    document.getElementById("inchiCompare").innerHTML = "";
    originalImg = document.getElementById("original_image");
    if (originalImg.firstChild)
        originalImg.removeChild(originalImg.firstChild);
    disconnectedImg = document.getElementById("disconnected_image");
    if (disconnectedImg.firstChild)
        disconnectedImg.removeChild(disconnectedImg.firstChild);
    document.getElementById("original_inchi").innerHTML = "";
    document.getElementById("disconnected_inchi").innerHTML = "";
    document.getElementById("input").value = "";
    console.log("cleared");
}


async function submitInput() {
    inputMol = document.getElementById("input").value;
    pyodide = await pyodidePromise;
    module = pyodide.pyimport("main");
    module.process(inputMol)
}
