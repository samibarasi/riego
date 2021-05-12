import React, { ChangeEventHandler, FormEventHandler, useState } from 'react'
import { Button, Form, Grid, GridColumn, Header, Message, Segment } from 'semantic-ui-react'

interface PropsType {
    onSuccess: () => void
}
export default function LoginForm(props: PropsType) {

    const [state, setstate] = useState(
        {
            identity: '',
            password: ''
        }
    )

    const handleLogin:FormEventHandler<HTMLFormElement> = async (e) => {
        e.preventDefault();
    
        const data = new FormData()
        data.append('identity', state.identity);
        data.append('password', state.password);

        const response = await fetch('http://localhost:8080/Vx-glzm7pbuuqeqP/api/login', {
            method: 'POST',
            body: data
        });
        const json = await response.json();

        if (json.status === 'success') {
            props.onSuccess();
        }
    }

    const changeHandler:ChangeEventHandler<HTMLInputElement> = ({ target }) => {
        setstate(() => ({
            ...state,
            [target.name]: target.value
        }))
    };

    return (
        <Grid textAlign="center" style={{ height: '100vh' }} verticalAlign="middle">
            <GridColumn>
                <Header as="h2" color="teal">
                    Log-in to your account
                </Header>
                    <Form onSubmit={handleLogin}>
                        <Segment stacked basic>
                            <Form.Input fluid icon="user" name="identity" iconPosition="left" placeholder="Identity" onChange={ changeHandler } />
                            <Form.Input fluid icon="lock" name="password" type="password" iconPosition="left" placeholder="password" onChange={ changeHandler }  />
                            <Button type='submit' color="teal" fluid size="large">
                                Login
                        </Button>
                        </Segment>
                    </Form>
                
                <Message>
                    New to us? <a href='#'>Sign Up</a>
                </Message>
            </GridColumn>
        </Grid>

    )
}
