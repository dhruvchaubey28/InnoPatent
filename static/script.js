document.getElementById('search-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const query = document.getElementById('query').value;
    
    // Fetch results from the backend
    const response = await fetch(`/search?query=${encodeURIComponent(query)}`);
    const data = await response.json();

    const resultsDiv = document.getElementById('results');
    const queriesDiv = document.getElementById('stored-queries');

    // Clear previous results and stored queries
    resultsDiv.innerHTML = '<h2>Search Results:</h2>';
    queriesDiv.innerHTML = '<h3>Stored Search Queries:</h3>';

    if (data.error) {
        resultsDiv.innerHTML += `<p>${data.error}</p>`;
    } else {
        // Display patent results (titles, authors, descriptions, images) returned by the backend
        if (data.results && data.results.length > 0) {
            data.results.forEach(result => {
                // Create a container for each patent result
                const resultDiv = document.createElement('div');
                resultDiv.classList.add('result-item');
                
                // Create a clickable link for each patent title
                const titleLink = document.createElement('a');
                titleLink.href = `https://patents.google.com/patent/${result.id}/en`;  // The patent full URL
                titleLink.textContent = result.title;  // The patent title
                titleLink.target = '_blank';  // Open the link in a new tab

                // Create the authors section (bold font)
                const authors = document.createElement('p');
                authors.classList.add('authors');
                authors.textContent = `Authors: ${result.authors}`;  // Display authors

                // Create the description section
                const description = document.createElement('p');
                description.textContent = `Description: ${result.description}`;  // Display description

                // Add image (if available)
                if (result.image) {
                    const image = document.createElement('img');
                    image.src = result.image;  // Image URL
                    resultDiv.appendChild(image);
                }

                // Append title, authors, and description
                resultDiv.appendChild(titleLink);
                resultDiv.appendChild(authors);
                resultDiv.appendChild(description);

                // Append the result item to the results section
                resultsDiv.appendChild(resultDiv);
            });
        } else {
            resultsDiv.innerHTML += '<p>No results found.</p>';
        }

        // Display stored search queries
        const queryList = data.queries.map(query => `<li>${query}</li>`).join('');
        queriesDiv.innerHTML += `<ul>${queryList}</ul>`;
    }
});
