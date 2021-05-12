import React, { useEffect, useReducer } from 'react'
import { Button, Icon, Item, ItemGroup, Segment } from 'semantic-ui-react'
import UserEdit from './UserEdit';

export type UserType = {
    id: number
    identity: string
    created_at: string
    password: string
    remember_me: boolean
}

type StateType = {
    list: UserType[],
    user: UserType | undefined,
    error: boolean,
    view: 'edit' | 'list'
}

type ActionType =
    | { type: 'NEW' }
    | { type: 'LIST', list: UserType[] }
    | { type: 'EDIT', user: UserType }
    | { type: 'DELETE', user: UserType };

const dataReducer = (state: StateType, action: ActionType): StateType => {
    switch (action.type) {
        case 'NEW':
            return { ...state };
        case 'LIST':
            return { ...state, list: action.list, view: 'list' }
        case 'EDIT':
            return { ...state, user: action.user, view: 'edit' }
        case 'DELETE':
            return { ...state, view: 'list' }
    }
}

const initialState: StateType = {
    list: [],
    user: undefined,
    error: false,
    view: 'list'
}

export default function UserList() {

    const [state, dispatch] = useReducer(dataReducer, initialState);

    useEffect(() => {
        let mounted = true
        const getUsers = () => {
            fetch('http://localhost:8080/Vx-glzm7pbuuqeqP/api/users')
                .then(response => response.json())
                .then(data => {
                    console.log(data)
                    if (mounted)
                        dispatch({ type: 'LIST', list: data });
                });
        }
        getUsers();
        return () => {
            console.log("...unmounting");
            mounted = false;
        }
    }, [])

    return (
        <>
            <h1>Users</h1>
            <Segment inverted>
                <code>
                    <pre>{JSON.stringify(state, null, 2)}</pre>
                </code>
            </Segment>
            <ItemGroup divided>
                {state.list.map((value, index) => {
                    return (
                        <Item key={index} >
                            <Item.Content>
                                <Icon name='user' size="large" />
                                <Item.Header>
                                    { value.id } - { value.identity } 
                                </Item.Header>
                                <Item.Meta>
                                    { new Date(value.created_at).toLocaleString('de-DE') }
                                </Item.Meta>
                            </Item.Content>
                            
                            <Button primary onClick={() => dispatch({type:'EDIT', user: value})}>Edit</Button>
                            
                        </Item>
                    )
                })}
            </ItemGroup>
            {(state.view === 'edit') &&
                <UserEdit user={state.user} />
            }
            
        </>
    )
}
