const forms = document.querySelector(".forms"),
      pwShowHide = document.querySelectorAll(".eye-icon"),
      links = document.querySelectorAll(".link");

pwShowHide.forEach(eyeIcon => {
    eyeIcon.addEventListener("click", () => {
        let pwFields = eyeIcon.parentElement.parentElement.querySelectorAll(".password");

        pwFields.forEach(password => {
            if (password.type === "password") {
                password.type = "text";
                eyeIcon.classList.replace("bx-hide", "bx-show");
            } else {
                password.type = "password";
                eyeIcon.classList.replace("bx-show", "bx-hide");
            }
        });
    });
});

links.forEach(link => {
    link.addEventListener("click", e => {
        e.preventDefault();
        forms.classList.toggle("show-signup");
    });
});

// Firebase login/signup logic
document.querySelector(".login form").addEventListener("submit", (e) => {
    e.preventDefault();
    const email = document.querySelector(".login .input").value;
    const password = document.querySelector(".login .password").value;

    firebase.auth().signInWithEmailAndPassword(email, password)
        .then(userCredential => userCredential.user.getIdToken())
        .then(idToken => {
            document.cookie = `token=${idToken}; path=/`;
            window.location.href = "/dashboard";
        })
        .catch(error => {
            alert("Login error: " + error.message);
        });
});

document.querySelector(".signup form").addEventListener("submit", (e) => {
    e.preventDefault();
    const email = document.querySelector(".signup .input").value;
    const password = document.querySelectorAll(".signup .password")[0].value;
    const confirmPassword = document.querySelectorAll(".signup .password")[1].value;

    if (password !== confirmPassword) {
        alert("Passwords do not match!");
        return;
    }

    firebase.auth().createUserWithEmailAndPassword(email, password)
        .then(userCredential => {
            alert("Signup successful!");
            forms.classList.remove("show-signup");
        })
        .catch(error => {
            alert("Signup error: " + error.message);
        });
});

function logoutUser() {
    firebase.auth().signOut().then(() => {
        document.cookie = "token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        window.location.href = "/logout";
    }).catch(error => {
        alert("Logout error: " + error.message);
    });
}

// Automatically redirect unauthorized users
firebase.auth().onAuthStateChanged((user) => {
    const protectedRoutes = ["/dashboard", "/image"];
    if (!user && protectedRoutes.includes(window.location.pathname)) {
        window.location.href = "/login";
    }
});
// Profile update logic
document.getElementById("updateProfile").addEventListener("click", async (event) => {
    event.preventDefault(); // Prevents unintended form submission

    const userId = firebase.auth().currentUser.uid;
    const updatedData = {
        name: document.getElementById("name").value,
        age: document.getElementById("age").value,
        weight: document.getElementById("weight").value,
        height: document.getElementById("height").value,
        gender: document.getElementById("gender").value,
        activityLevel: document.getElementById("activityLevel").value
    };

    try {
        await firebase.firestore().collection("users").doc(userId).update(updatedData);
        alert("Profile updated successfully!");
        
        // Redirect to profile.html after successful update
        window.location.href = "profile.html";
    } catch (error) {
        console.error("Error updating profile:", error);
        alert("Failed to update profile.");
    }
});
firebase.auth().onAuthStateChanged(user => {
    if (user) {
        firebase.firestore().collection("users").doc(user.uid).get()
            .then(doc => {
                if (doc.exists) {
                    document.getElementById("profileName").innerText = doc.data().name;
                    document.getElementById("profileAge").innerText = doc.data().age;
                    document.getElementById("profileWeight").innerText = doc.data().weight;
                    document.getElementById("profileHeight").innerText = doc.data().height;
                    document.getElementById("profileGender").innerText = doc.data().gender;
                    document.getElementById("profileActivity").innerText = doc.data().activityLevel;
                }
            });
    }
});
