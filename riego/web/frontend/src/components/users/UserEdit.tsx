import React, { useEffect, useState } from 'react'
import { Button, Checkbox, Divider, Form, Header, Icon } from 'semantic-ui-react';
import { UserType } from './UserList';

interface PropsType {
    user: UserType | undefined
}

const initialState: UserType = {
    id: -1,
    identity: '',
    password: '',
    created_at: '',
    remember_me: false
}

export default function UserEdit(props: PropsType) {

    const [user, setUser] = useState(initialState)

    useEffect(() => {
        let mounted = true;

        const getUserById = async (id: number) => {
            const response = await fetch(`http://localhost:8080/Vx-glzm7pbuuqeqP/api/user/${id}`)
            const data = await response.json();
            console.log(data)
            if (mounted)
                setUser(data);
        }

        if (props.user)
            getUserById(props.user.id);

        return () => {
            mounted = false;
        }
    }, [props.user])
    return (
        <Form>
            <Form.Field>
                <Form.Input label="Identity:" name="identity" defaultValue={user.identity} />
            </Form.Field>
            <Divider horizontal>
                <Header as='h4'>
                    <Icon name='lock' />
                    Change Password
                </Header>
            </Divider>
            <Form.Field>
                <Form.Input label="New Password:" name="password" />
            </Form.Field>
            <Form.Field>
                <Form.Input label="Repeat New Password:" name="repeatpassword" />
            </Form.Field>
            <Form.Field>
                <Checkbox label='Remember Me' defaultValue={user.remember_me} />
            </Form.Field>
            <Button type='submit'>Submit</Button>
        </Form>
    )
}
