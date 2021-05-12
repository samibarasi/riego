import React, { useState } from 'react';
import 'semantic-ui-css/semantic.min.css';
import { Container } from 'semantic-ui-react';
import './App.css';
import LoginForm from './components/security/LoginForm';
import UserList from './components/users/UserList';


const initialState = {
    loggedIn: false
}

function App() {

    const [state, setState] = useState(initialState)

    const successHandler = () => {
        console.log("logged in");
        setState({ loggedIn: true })
    }
        
    return (
        <div className="App">
            <header className="App-header">

            </header>
            <main>
                <Container>
                    {state.loggedIn && <UserList />}
                    {!state.loggedIn && <LoginForm onSuccess={ successHandler }/>}
                </Container>
            </main>
        </div>

    );
}

export default App;
